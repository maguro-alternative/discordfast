import os
import base64
import hashlib
import hmac
from fastapi import APIRouter
from starlette.requests import Request
import json

router = APIRouter()

consumer_secret = os.environ["TWITTER_CLIENT_SECRET"]

@router.get('/api/webhook')
async def webhook_challenge(request:Request):
	params = request.query_params
	print(params)
	if 'crc_token' in params:
		sha256_hash_digest = hmac.new(
			consumer_secret.encode(), 
			msg = params.get('crc_token').encode(), 
			digestmod = hashlib.sha256
		).digest()
		digested = base64.b64encode(sha256_hash_digest).decode()
		response = {
			'response_token':f'sha256={digested}'
		}
		return response
	else:
		return json.dumps({'error':'No Content'})