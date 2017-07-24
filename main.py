import sys
from PyQt5 import QtWidgets
from git_rewrite_date import GitRewriteDate

def main():
	app = QtWidgets.QApplication(sys.argv)
	w = GitRewriteDate()
	w.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
