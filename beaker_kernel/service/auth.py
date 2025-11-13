from functools import lru_cache

import base64
import boto3
import json
import requests
from traitlets import Unicode, Bool, Enum

from jupyter_server.auth.authorizer import Authorizer, AllowAllAuthorizer
from jupyter_server.auth.identity import IdentityProvider, User

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None


class CognitoHeadersIdentityProvider(IdentityProvider):

    auth_mode = Enum(
        ['alb', 'app', 'auto'],
        default_value='auto',
        config=True,
        help="Authentication mode: 'alb' (ALB-level), 'app' (app-level), 'auto' (try both). Defaults to 'auto' for backward compatibility.",
    )

    cognito_jwt_header = Unicode(
        default_value="X-Amzn-Oidc-Data",
        config=True,
        help="Header containing the cognito JWT encoded grants (ALB mode)",
    )

    cognito_identity_header = Unicode(
        default_value="X-Amzn-Oidc-Identity",
        config=True,
        help="Header containing the cognito user identity (ALB mode)",
    )

    cognito_accesstoken_header = Unicode(
        default_value="X-Amzn-Oidc-Accesstoken",
        config=True,
        help="Header containing the cognito active access token (ALB mode)",
    )

    app_user_id_header = Unicode(
        default_value="X-Beaker-User-Id",
        config=True,
        help="Header containing user ID (app-level auth mode)",
    )

    app_access_token_header = Unicode(
        default_value="X-Beaker-Access-Token",
        config=True,
        help="Header containing access token (app-level auth mode)",
    )

    app_id_token_header = Unicode(
        default_value="X-Beaker-Id-Token",
        config=True,
        help="Header containing ID token (app-level auth mode)",
    )

    user_pool_id = Unicode(
        default_value="",
        config=True,
        help="AWS Cognito User Pool ID (optional - only used for enriching user info)",
    )

    cognito_region = Unicode(
        default_value="",
        config=True,
        help="AWS Cognito Region (optional, auto-detected from user_pool_id if not set)",
    )

    verify_jwt_signature = Bool(
        default_value=True,
        config=True,
        help="Whether the jwt signature should be verified",
    )


    @lru_cache
    def _get_elb_key(self, region: str, kid: str) -> str:
        key_url = f"https://public-keys.auth.elb.{region}.amazonaws.com/{kid}"
        pubkey = requests.get(key_url).text
        return pubkey

    @lru_cache
    def _get_cognito_jwks(self, user_pool_id: str, region: str) -> dict:
        """Fetch JWKS from Cognito well-known endpoint"""
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()

    def _get_cognito_region(self) -> str:
        """Get Cognito region from config or default to us-east-1"""
        if self.cognito_region:
            return self.cognito_region
        
        # Default to us-east-1 if not set
        return "us-east-1"

    @lru_cache
    def _verify_jwt(self, jwt_data: str):
        """Verify ALB-signed JWT"""
        if pyjwt is not None:
            header, body = [json.loads(base64.b64decode(f).decode('utf-8')) for f in jwt_data.split('.')[0:2]]
            self.log.warning(header)
            self.log.warning(body)
            signer: str = header.get("signer")
            region = signer.split(':')[3]
            kid: str = header.get("kid")
            pubkey = self._get_elb_key(region, kid)
            payload = pyjwt.decode(jwt_data, key=pubkey, algorithms=["ES256", "RS256"])
            self.log.warning(payload)
            return payload

    def _verify_cognito_id_token(self, jwt_data: str) -> dict | None:
        """Verify Cognito ID token using JWKS"""
        if not self.user_pool_id:
            if self.verify_jwt_signature:
                self.log.warning("Cannot verify Cognito ID token: user_pool_id not set")
            return None
        
        if pyjwt is None:
            if self.verify_jwt_signature:
                self.log.warning("Cannot verify Cognito ID token: pyjwt not installed")
            return None

        try:
            # Decode header to get kid
            header_data = jwt_data.split('.')[0]
            header = json.loads(base64.urlsafe_b64decode(header_data + '==').decode('utf-8'))
            kid = header.get('kid')
            
            if not kid:
                self.log.warning("JWT header missing 'kid' claim")
                return None

            # Get region
            region = self._get_cognito_region()
            
            # Fetch JWKS
            try:
                jwks = self._get_cognito_jwks(self.user_pool_id, region)
            except Exception as e:
                self.log.error(f"Failed to fetch Cognito JWKS: {e}")
                if self.verify_jwt_signature:
                    return None
                # If verification disabled, decode without verification
                return pyjwt.decode(jwt_data, options={"verify_signature": False})

            # Find the key with matching kid
            public_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format for pyjwt
                    from cryptography.hazmat.primitives.asymmetric import rsa
                    from cryptography.hazmat.backends import default_backend
                    import cryptography.hazmat.primitives.serialization as serialization
                    
                    # Extract RSA components from JWK
                    n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), 'big')
                    e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), 'big')
                    
                    # Build RSA public key
                    public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
                    break

            if not public_key:
                self.log.warning(f"No matching key found for kid: {kid}")
                if self.verify_jwt_signature:
                    return None
                return pyjwt.decode(jwt_data, options={"verify_signature": False})

            # Verify and decode token
            if self.verify_jwt_signature:
                # Get expected issuer and audience
                expected_issuer = f"https://cognito-idp.{region}.amazonaws.com/{self.user_pool_id}"
                # Decode without verification first to get audience
                unverified = pyjwt.decode(jwt_data, options={"verify_signature": False})
                expected_audience = unverified.get('aud') or self.user_pool_id
                
                payload = pyjwt.decode(
                    jwt_data,
                    public_key,
                    algorithms=["RS256"],
                    issuer=expected_issuer,
                    audience=expected_audience,
                )
            else:
                payload = pyjwt.decode(jwt_data, options={"verify_signature": False})

            return payload

        except pyjwt.exceptions.InvalidTokenError as e:
            self.log.warning(f"Invalid Cognito ID token: {e}")
            if self.verify_jwt_signature:
                return None
            # If verification disabled, try to decode anyway
            try:
                return pyjwt.decode(jwt_data, options={"verify_signature": False})
            except:
                return None
        except Exception as e:
            self.log.error(f"Error verifying Cognito ID token: {e}")
            if self.verify_jwt_signature:
                return None
            try:
                return pyjwt.decode(jwt_data, options={"verify_signature": False})
            except:
                return None

    def _get_user_id_from_token(self, jwt_data: str) -> str | None:
        """Extract user_id from JWT claims"""
        if not jwt_data or pyjwt is None:
            return None
        try:
            # Decode without verification to get claims
            payload = pyjwt.decode(jwt_data, options={"verify_signature": False})
            # Cognito ID tokens typically have 'sub' claim for user ID
            return payload.get('sub') or payload.get('username')
        except Exception as e:
            self.log.debug(f"Could not extract user_id from token: {e}")
            return None

    def _get_auth_from_alb(self, handler) -> tuple[str | None, str | None, str | None]:
        """Extract auth info from ALB headers"""
        jwt_data = handler.request.headers.get(self.cognito_jwt_header, None)
        user_id = handler.request.headers.get(self.cognito_identity_header, None)
        access_token = handler.request.headers.get(self.cognito_accesstoken_header, None)
        return jwt_data, user_id, access_token

    def _get_auth_from_app(self, handler) -> tuple[str | None, str | None, str | None]:
        """Extract auth info from app-level headers"""
        user_id = handler.request.headers.get(self.app_user_id_header, None)
        access_token = handler.request.headers.get(self.app_access_token_header, None)
        jwt_data = handler.request.headers.get(self.app_id_token_header, None)
        return jwt_data, user_id, access_token


    def _get_user(self, user_id, access_token):
        """
        Get user info from Cognito if user_pool_id is set, otherwise create basic User.
        user_pool_id is optional - if not set, creates basic User from user_id.
        """
        # If user_pool_id is not set, create basic User object
        if not self.user_pool_id:
            self.log.debug(f"user_pool_id not set, creating basic User from user_id: {user_id}")
            return User(
                username=user_id,
                name=user_id,
                display_name=user_id,
            )

        # Try to get enriched user info from Cognito
        try:
            cognito_client = boto3.client('cognito-idp')
            response = cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=user_id
            )

            user_attributes = {attr['Name']: attr['Value'] for attr in response.get('UserAttributes', [])}
            username = user_attributes.get('preferred_username') or user_attributes.get('email') or user_id

            return User(
                username=username,
                name=user_attributes.get('name', username),
                display_name=user_attributes.get('given_name', username),
            )
        except Exception as e:
            self.log.warning(f"Failed to get cognito user info for {user_id}: {e}, falling back to basic User")
            # Fall back to basic User if Cognito lookup fails
            return User(
                username=user_id,
                name=user_id,
                display_name=user_id,
            )


    async def get_user(self, handler) -> User | None:
        """Main entry point - supports both ALB and app-level authentication"""
        jwt_data = None
        user_id = None
        access_token = None
        is_alb_mode = False

        # Determine which headers to read based on auth_mode
        if self.auth_mode == 'alb':
            jwt_data, user_id, access_token = self._get_auth_from_alb(handler)
            is_alb_mode = True
        elif self.auth_mode == 'app':
            jwt_data, user_id, access_token = self._get_auth_from_app(handler)
            is_alb_mode = False
        else:  # auto mode
            # Try ALB first, then fall back to app-level
            jwt_data, user_id, access_token = self._get_auth_from_alb(handler)
            if not user_id:
                jwt_data, user_id, access_token = self._get_auth_from_app(handler)
                is_alb_mode = False
            else:
                is_alb_mode = True

        # If still no user_id, try extracting from JWT if available
        if not user_id and jwt_data:
            user_id = self._get_user_id_from_token(jwt_data)

        # Missing user_id means authentication failed
        if not user_id:
            return None

        # Handle JWT verification
        if jwt_data:
            if is_alb_mode:
                # ALB mode: verify ALB-signed JWT
                if pyjwt is None:
                    if self.verify_jwt_signature:
                        self.log.warning("Unable to verify JWT signature as package 'pyjwt' is not installed.")
                        return None
                elif self.verify_jwt_signature:
                    try:
                        self._verify_jwt(jwt_data)
                    except pyjwt.exceptions.InvalidTokenError as e:
                        self.log.warning(f"Error attempting to verify ALB JWT token: {e}")
                        return None
            else:
                # App mode: verify Cognito ID token
                if self.verify_jwt_signature:
                    verified_payload = self._verify_cognito_id_token(jwt_data)
                    if verified_payload is None:
                        # Verification failed and was required
                        return None

        # For ALB mode, access_token is required
        if is_alb_mode and not access_token:
            return None

        # For app mode, access_token is optional (BeakerHub already authenticated)
        # If access_token is missing, we can still create a User from user_id

        user = self._get_user(user_id, access_token)
        return user
