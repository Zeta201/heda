from dotenv import load_dotenv
import os
from github import Github

load_dotenv()


GITHUB_ORG = os.environ.get("GITHUB_ORG") 
ADMIN_GITHUB_TOKEN = os.environ.get("GITHUB_ADMIN_TOKEN")  

if not ADMIN_GITHUB_TOKEN:
    raise RuntimeError("Missing environment variables: GITHUB_ADMIN_TOKEN")

def get_admin_gh():
    return Github(ADMIN_GITHUB_TOKEN)

def get_admin_org():
    gh = Github(ADMIN_GITHUB_TOKEN)
    return gh.get_organization(GITHUB_ORG)


