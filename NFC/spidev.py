import nfc

def on_connect(tag):
    print("NFC TAG CONNECTED GG")
    print(tag)
    return False

clf =nfc.ContactlessFrontend('usb')
try:
    clf.connect(rdwr={'on-connect': on_connect})
finally:
    clf.close()     