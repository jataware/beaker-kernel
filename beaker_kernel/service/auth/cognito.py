import base64
import boto3
import boto3.exceptions
import json
import os
import requests
from functools import lru_cache
from traitlets import Unicode, Bool, default
from urllib.parse import urlencode

from jupyter_server.auth.identity import User
from jupyter_server.base.handlers import JupyterHandler

from . import BeakerAuthorizer, BeakerIdentityProvider, RoleBasedUser, current_request, current_user

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None


class CognitoLogoutHandler(JupyterHandler):
    def get(self, *args, **kwargs):
        # Clear authentication cookies
        # If no prefix is provided, remove all cookies
        cookie_prefix = getattr(self.identity_provider, 'auth_cookie_prefix', '')
        auth_cookies = [cookie_name for cookie_name in self.cookies if cookie_name.startswith(cookie_prefix)]
        for cookie_name in auth_cookies:
            self.clear_cookie(cookie_name)

        # Fetch info needed for redirect
        pool_info = self.identity_provider.user_pool_details
        client_info = self.identity_provider.client_details
        auth_domain = pool_info.get("Domain", None)
        client_id = client_info.get("ClientId", None)

        # Use first logout url defined
        logout_url = next(iter(client_info.get("LogoutURLs", [])), None)
        if auth_domain and client_id:
            query_args = {"client_id": client_id}
            if logout_url:
                query_args["logout_uri"] = logout_url
            location = f"https://{auth_domain}/logout?{urlencode(query_args)}"
        else:
            location = "/"

        self.set_header("Location", location)
        self.set_status(302)
        self.finish()


class LoggedOutHandler(JupyterHandler):
    def get(self, *args, **kwargs):
        self.write("""
<html>
<body>
<h1>You have successfully logged out</h1>
<a href="/">Click here to return to the application.</a>
</body>
</html>
""")
        self.finish()


class CognitoHeadersIdentityProvider(BeakerIdentityProvider):

    logout_handler_class = CognitoLogoutHandler

    def get_handlers(self):
        handlers = super().get_handlers()
        handlers.append(
            (r'/loggedout', LoggedOutHandler)
        )
        return handlers

    def __init__(self, **kwargs):
        self.cognito_client = boto3.client('cognito-idp')
        try:
            user_pool_details = self.cognito_client.describe_user_pool(
                UserPoolId=self.user_pool_id
            )
            self.user_pool_details = user_pool_details.get("UserPool", None)
        except boto3.exceptions.Boto3Error as err:
            self.log(err)
            self.user_pool_details = None
        if self.cognito_client_id:
            try:
                client_details = self.cognito_client.describe_user_pool_client(
                    UserPoolId=self.user_pool_id,
                    ClientId=self.cognito_client_id,
                )
                self.client_details = client_details.get("UserPoolClient", None)
            except boto3.exceptions.Boto3Error as err:
                self.log.error(err)
                self.client_details = None
        super().__init__(**kwargs)

    auth_cookie_prefix = Unicode(
        default_value="AuthSessionCookie",
        config=True,
        help="Name/prefix for cookie used to track authenticated session. If blank, remove all cookies."
    )

    cognito_jwt_header = Unicode(
        default_value="X-Amzn-Oidc-Data",
        config=True,
        help="Name of header containing the cognito JWT encoded grants",
    )

    cognito_identity_header = Unicode(
        default_value="X-Amzn-Oidc-Identity",
        config=True,
        help="Name of header containing the cognito user identity",
    )

    cognito_accesstoken_header = Unicode(
        default_value="X-Amzn-Oidc-Accesstoken",
        config=True,
        help="Name of header containing the cognito active access token",
    )

    user_pool_id = Unicode(
        default_value="",
        config=True,
        help="AWS Cognito User Pool ID",
    )

    @default("user_pool_id")
    def _default_user_pool_id(self):
        return os.getenv("COGNITO_USER_POOL_ID")

    cognito_client_id = Unicode(
        config=True,
        help="AWS Cognito client_id",
    )

    @default("cognito_client_id")
    def _default_cognito_client_id(self):
        return os.getenv("COGNITO_CLIENT_ID")


    verify_jwt_signature = Bool(
        default_value=True,
        config=True,
        help="Whether the jwt signature from cognito should be verified",
    )

    @property
    def login_available(self):
        """Cognito login always happens prior to the identity provider, will happen automatically."""
        return False

    @lru_cache
    def _get_elb_key(self, region: str, kid: str) -> str:
        key_url = f"https://public-keys.auth.elb.{region}.amazonaws.com/{kid}"
        pubkey = requests.get(key_url).text
        return pubkey


    @lru_cache
    def _verify_jwt(self, jwt_data: str):
        if pyjwt is not None:
            header, body = [json.loads(base64.b64decode(f).decode('utf-8')) for f in jwt_data.split('.')[0:2]]
            signer: str = header.get("signer")
            region = signer.split(':')[3]
            kid: str = header.get("kid")
            pubkey = self._get_elb_key(region, kid)
            payload = pyjwt.decode(jwt_data, key=pubkey, algorithms=["ES256", "RS256"])
            return payload


    @lru_cache
    def _get_cognito_user(self, user_id, access_token):
        # Access token is provided as an argument to ensure that auth info is refetched (misses cache) if the access token changes.
        try:
            response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=user_id
            )

            user_attributes = {attr['Name']: attr['Value'] for attr in response.get('UserAttributes', [])}
            username = user_attributes.get('preferred_username') or user_attributes.get('email') or user_id

            return RoleBasedUser(
                username=username,
                name=user_attributes.get('name', username),
                display_name=user_attributes.get('given_name', username),
                roles=[],
            )
        except Exception as e:
            self.log.warning(f"Failed to get cognito user info for {user_id}: {e}")
            return None


    async def get_user(self, handler) -> User|None:
        current_request.set(handler.request)


        jwt_data: str = handler.request.headers.get(self.cognito_jwt_header, None)
        user_id: str = handler.request.headers.get(self.cognito_identity_header, None)
        access_token: str = handler.request.headers.get(self.cognito_accesstoken_header, None)

        match pyjwt, self.verify_jwt_signature, jwt_data:
            case (None, _, _):
                self.log.warning("Unable to verify JWT signature as package 'pyjwt' is not installed.")
            case (_, _, None):
                self.log.warning("Unable to verify JWT signature as no signature could be found.")
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

        user = self._get_cognito_user(user_id, access_token)
        if user:
            current_user.set(user)
        return user


class CognitoAuthorizer(BeakerAuthorizer):
    def is_authorized(self, handler, user, action, resource):
        # TODO: More explicit rules
        return 'admin' in user.roles


identity_provider = CognitoHeadersIdentityProvider
authorizer = CognitoAuthorizer
