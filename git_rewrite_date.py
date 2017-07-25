from PyQt5 import QtGui, QtWidgets, QtCore, uic
from my_git import *
from threading import Thread
import hashlib, urllib.request

class GitRewriteDate(QtWidgets.QMainWindow):
	def __init__(self):
		super(GitRewriteDate, self).__init__()
		uic.loadUi('main.ui', self)
		self.splitter.setStretchFactor(0, 1)
		self.splitter.setStretchFactor(1, 0)
		self.selectors.hide()

		label = QtWidgets.QLabel()
		label.setObjectName("progress_label")
		self.statusbar.addWidget(label)

		self.commit_datetime = []
		self.current_selected_row = -1


	def path_selector_dialog(self, clicked):
		pathDialog = QtWidgets.QFileDialog()
		path = str(pathDialog.getExistingDirectory(caption = "Select git directory"))

		try:
			self.mygit.updated.disconnect()
			self.mygit.finished.disconnect()
		except Exception as e:
			pass

		self.mygit = MyGit(path)
		if not self.mygit.is_valid():
			QtWidgets.QMessageBox.information(self, "Informacion", "This folder doesn't seem to contain a git repository.", QtWidgets.QMessageBox.Ok)
			return

		if self.mygit.is_dirty():
			QtWidgets.QMessageBox.information(self, "Informacion", "This repository seems to be dirty. Maybe you have unstaged changes?", QtWidgets.QMessageBox.Ok)
			return

		self.mygit.updated.connect(self.update_statusbar)
		self.mygit.finished.connect(self.clean_ui)

		self.path.setText(path)


	def load_branches(self, path):
		self.branches.clear()
		self.branches.addItems(map(lambda v: v.name, self.mygit.repo.branches))

	def load_commits(self, branch):
		self.commits.setRowCount(len(list(self.mygit.repo.iter_commits(branch))))
		self.commits.setColumnCount(3)

		image_height = 40
		images_cache = {}

		#author, authored_datetime, message, hexsha
		for idx, commit in enumerate(self.mygit.repo.iter_commits(branch)):
			avatar = "http://gravatar.com/avatar/%s?s=%spx" % (hashlib.md5(commit.author.email.encode('utf-8')).hexdigest(), image_height)

			if avatar not in images_cache:
				try:
					images_cache[avatar] = urllib.request.urlopen(avatar).read()
				except Exception as e:
					images_cache[avatar] = None

			pixmap = QtGui.QPixmap()
			if images_cache[avatar] is not None:
				pixmap.loadFromData(images_cache[avatar])
			img_label =  QtWidgets.QLabel()
			img_label.setPixmap(pixmap)

			widget = QtWidgets.QWidget()
			label =  QtWidgets.QLabel("%s" % commit.author.name)
			layout = QtWidgets.QHBoxLayout()
			layout.addWidget(img_label)
			layout.addWidget(label)
			layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
			widget.setLayout(layout)
			self.commits.setCellWidget(idx, 0, widget)

			widget = QtWidgets.QWidget()
			message_label =  QtWidgets.QLabel("%s" % commit.message.strip())
			hash_label = QtWidgets.QLabel("%s" % commit.hexsha)
			layout = QtWidgets.QVBoxLayout()
			layout.addWidget(message_label)
			layout.addWidget(hash_label)
			layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
			widget.setLayout(layout)
			self.commits.setCellWidget(idx, 1, widget)

			widget = QtWidgets.QWidget()
			widget.setObjectName("dates_holder")
			newlabel =  QtWidgets.QLabel("")
			newlabel.setObjectName("newdatetime")
			label =  QtWidgets.QLabel("%s" % commit.authored_datetime)
			label.setObjectName("datetime")
			layout = QtWidgets.QVBoxLayout()
			layout.addWidget(newlabel)
			layout.addWidget(label)
			layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
			widget.setLayout(layout)
			self.commits.setCellWidget(idx, 2, widget)

			self.commit_datetime.append({
				"hash": commit.hexsha,
				"datetime": commit.authored_datetime,
				"newdatetime": None
			})

		self.commits.resizeColumnsToContents()
		self.commits.resizeRowsToContents()

	def show_selectors(self, row, col):
		self.selectors.show()
		self.current_selected_row = row

		newdatetime = self.commit_datetime[row]["datetime"]

		self.date.blockSignals(True)
		self.date.setSelectedDate(newdatetime)
		self.date.blockSignals(False)

		self.time.blockSignals(True)
		self.time.setTime(newdatetime.time())
		self.time.blockSignals(False)

	def date_changed(self, date):
		newdatetime = self.commit_datetime[self.current_selected_row]["datetime"].replace(
			year = date.year(),
			month = date.month(),
			day = date.day()
		)
		self.commit_datetime[self.current_selected_row]["newdatetime"] = newdatetime
		self.update_datetime_cell()

	def time_changed(self, time):
		newdatetime = self.commit_datetime[self.current_selected_row]["datetime"].replace(
			hour = time.hour(),
			minute = time.minute(),
			second = time.second()
		)
		self.commit_datetime[self.current_selected_row]["newdatetime"] = newdatetime
		self.update_datetime_cell()

	def update_datetime_cell(self):
		newdatetime = self.commit_datetime[self.current_selected_row]["newdatetime"]
		cell = self.commits.cellWidget(self.current_selected_row, 2)
		label = cell.findChild(QtWidgets.QLabel, "newdatetime")
		palette = label.palette();
		palette.setColor(label.foregroundRole(), QtCore.Qt.red)
		label.setPalette(palette)
		label.setText("%s" % newdatetime)

	def update_statusbar(self, data):
		label = self.statusbar.findChild(QtWidgets.QLabel, "progress_label")
		label.setText(data)

	def clean_ui(self):
		self.update_statusbar("")
		layouts = self.commits.findChildren(QtWidgets.QWidget, "dates_holder", QtCore.Qt.FindChildrenRecursively)
		for layout in layouts:
			newlabel = layout.findChild(QtWidgets.QLabel, "newdatetime")
			newdate = newlabel.text()
			if newdate is not "":
				label = layout.findChild(QtWidgets.QLabel, "datetime")
				label.setText(newdate)
				newlabel.setText("")

		for commit in self.commit_datetime:
			if commit["newdatetime"] is not None:
				commit["datetime"] = commit["newdatetime"]
				commit["newdatetime"] = None

	def rewrite(self):
		def _do(commits):
			self.mygit.rewrite_dates(commits)

		commits = filter(lambda x: x["newdatetime"] is not None, self.commit_datetime)
		thread = Thread(target = _do, args = (commits,))
		thread.start()
