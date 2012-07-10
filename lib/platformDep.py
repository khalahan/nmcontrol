import os
import platform

def getNamecoinDir():
	if platform.system() == "Darwin":
		return os.path.expanduser("~/Library/Application Support/Namecoin/")
	elif platform.system() == "Windows":
		return os.path.join(os.environ['APPDATA'], "Namecoin")
	return os.path.expanduser("~/.namecoin")

