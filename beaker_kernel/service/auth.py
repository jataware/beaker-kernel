from functools import lru_cache

import base64
import boto3
import json
import requests
from traitlets import Unicode, Bool

from jupyter_server.auth.authorizer import Authorizer, AllowAllAuthorizer
from jupyter_server.auth.identity import IdentityProvider, User

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None


class CognitoHeadersIdentityProvider(IdentityProvider):

    cognito_jwt_header = Unicode(
        default_value="X-Amzn-Oidc-Data",
        config=True,
        help="Header containing the cognito JWT encoded grants",
    )

    cognito_identity_header = Unicode(
        default_value="X-Amzn-Oidc-Identity",
        config=True,
        help="Header containing the cognito user identity",
    )

    cognito_accesstoken_header = Unicode(
        default_value="X-Amzn-Oidc-Accesstoken",
        config=True,
        help="Header containing the cognito active access token",
    )

    user_pool_id = Unicode(
        default_value="",
        config=True,
        help="AWS Cognito User Pool ID",
    )

    verify_jwt_signature = Bool(
        default_value=True,
        config=True,
        help="Whether the jwt signature from cognito should be verified",
    )


    @lru_cache
    def _get_elb_key(self, region: str, kid: str) -> str:
        key_url = f"https://public-keys.auth.elb.{region}.amazonaws.com/{kid}"
        pubkey = requests.get(key_url).text
        return pubkey


    @lru_cache
    def _verify_jwt(self, jwt_data: str):
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


    @lru_cache
    def _get_user(self, user_id, access_token):
        # Access token is provided as an argument to ensure that auth info is refetched (misses cache) if the access token changes.
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
            self.log.warning(f"Failed to get cognito user info for {user_id}: {e}")
            return None


    async def get_user(self, handler) -> User|None:
        jwt_data: str = handler.request.headers.get(self.cognito_jwt_header, None)
        user_id: str = handler.request.headers.get(self.cognito_identity_header, None)
        access_token: str = handler.request.headers.get(self.cognito_accesstoken_header, None)

        match pyjwt, self.verify_jwt_signature, jwt_data:
            case (None, _, _):
                self.log.warning("Unable to verify JWT signature as package 'pyjwt' is not installed.")
            case (_, _, None):
                self.log.warning("Unable to verify JWT signature as it is not found.")
            case (_, False, _):
                self.log.info("Skipping checking JWT signature due to configuration.")
            case (_, True, str()):
                try:
                    self._verify_jwt(jwt_data)
                except pyjwt.exceptions.InvalidTokenError as e:
                    self.log.warning(f"Error attempting to verify JWT token: {e}")
                    return None

        if not user_id or not access_token:
            return None

        user = self._get_user(user_id, access_token)
        return user
