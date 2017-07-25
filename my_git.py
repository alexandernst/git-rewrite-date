import git
import os, re, io
from git import Git, Repo
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject

class PipeIO(io.BytesIO):
	def __init__(self, updater_cb):
		io.BytesIO.__init__(self)
		self.updater_cb = updater_cb

	def write(self, b):
		buf = io.BytesIO.getbuffer(self).tobytes()
		progress = re.findall("(?<=\()\d+\/\d+(?=\))", buf.decode("utf-8"))

		try:
			self.updater_cb(progress[-1])
		except:
			pass

		return io.BytesIO.write(self, b)

class MyGit(QObject):
	updated = pyqtSignal(str)
	finished = pyqtSignal()

	def __init__(self, path):
		QObject.__init__(self)

		try:
			self.repo = Repo(path)
		except git.exc.NoSuchPathError as e:
			self.repo = None
		except git.exc.InvalidGitRepositoryError as e:
			self.repo = None

	def is_valid(self):
		return self.repo != None

	def is_dirty(self):
		return self.repo.is_dirty()

	def updater_cb(self, data):
		self.updated.emit(data)

	def rewrite_dates(self, commits):
		tpl = """
		if [ "$GIT_COMMIT" == "%s" ]; then
			export GIT_AUTHOR_DATE="%s"
			export GIT_COMMITTER_DATE="%s"
		fi
		"""

		stdout = PipeIO(self.updater_cb)

		s = ""
		for commit in commits:
			s += tpl % (
				commit["hash"],
				commit["newdatetime"].replace(tzinfo = None),
				commit["newdatetime"].replace(tzinfo = None)
			)

		thread = Thread(target = self.repo.git.filter_branch, args = ("-f", "--env-filter", s), kwargs = {"output_stream": stdout}) #, max_chunk_size = 30)
		thread.start()
		thread.join()
		self.finished.emit()
