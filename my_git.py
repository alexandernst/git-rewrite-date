import git
from git import Git, Repo
import os, re, io

class PipeIO(io.BytesIO):
	def __init__(self, cb):
		io.BytesIO.__init__(self)
		self.updater_cb = cb

	def write(self, b):
		buf = io.BytesIO.getbuffer(self).tobytes()
		progress = re.findall("(?<=\()\d+\/\d+(?=\))", buf.decode("utf-8"))

		try:
			self.updater_cb(progress[-1])
		except:
			pass

		return io.BytesIO.write(self, b)

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

	def is_clean(self):
		#TODO
		return True

	def rewrite_dates(self, commits, cb):
		tpl = """
		if [ "$GIT_COMMIT" == "%s" ]; then
			export GIT_AUTHOR_DATE="%s"
			export GIT_COMMITTER_DATE="%s"
		fi
		"""

		stdout = PipeIO(cb)

		s = ""
		for commit in commits:
			s += tpl % (
				commit["hash"],
				commit["newdatetime"].replace(tzinfo = None),
				commit["newdatetime"].replace(tzinfo = None)
			)
		self.repo.git.filter_branch("-f", "--env-filter", s, output_stream = stdout) #, max_chunk_size = 30)
