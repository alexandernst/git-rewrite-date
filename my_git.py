import git
from git import Git, Repo
import os

class MyGit():
	def __init__(self, path):
		try:
			self.repo = Repo(path)
		except git.exc.NoSuchPathError as e:
			self.repo = None
		except git.exc.InvalidGitRepositoryError as e:
			self.repo = None

	def is_valid(self):
		return self.repo != None
