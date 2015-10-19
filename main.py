from gi.repository import Gtk, GdkPixbuf, GObject, GLib
import vpnprotocol
import threading

#TODO: create self.vpn_connection

def is_valid_ip(string):
    try:
        if len(string) == 0: return False
        points = string.count(".")
        if not points == 3: return False
        domains = string.split(".", 4)
        for domain in domains:
            if len(domain) == 0: return False
            if len(domain) > 3: return False
            if int(domain) < 0: return False
            if int(domain) > 255: return False
        return True
    except Exception:
        return False

def is_valid_port(string):
    try:
        if len(string) == 0: return False
        if int(string) > 65535: return False
        return True
    except Exception:
        return False

class Setup(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "My Dialog", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.gladefile = 'setup.glade'
        self.gtk = Gtk.Builder()
        self.gtk.add_from_file(self.gladefile)
        box = self.get_content_area()
        box.add(self.gtk.get_object("setup"))

        self.server_radiobutton = self.gtk.get_object("server_radiobutton")
        self.client_radiobutton = self.gtk.get_object("client_radiobutton")
        self.address_message = self.gtk.get_object("address_message")
        self.ip_address_entry = self.gtk.get_object("ip_address_entry")
        self.port_entry = self.gtk.get_object("port_entry")
        self.shared_secret_entry = self.gtk.get_object("shared_secret_entry")

        self.server_radiobutton.connect("toggled", self.on_mode_toggled, "server")
        self.client_radiobutton.connect("toggled", self.on_mode_toggled, "client")
        self.ip_address_entry.connect("changed", self.on_inputs_changed)
        self.port_entry.connect("changed", self.on_inputs_changed)
        self.shared_secret_entry.connect("changed", self.on_inputs_changed)

        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        self.set_deletable(False)
        self.set_resizable(False)

        self.received_buffer = []

    def on_inputs_changed(self, entry):
        ip_address = self.ip_address_entry.get_text()
        port = self.port_entry.get_text()
        shared_secret = self.shared_secret_entry.get_text()

        # Test if inputs are ok!
        # Verify if ip address is in a valid format
        # Verify if port number is a valid choice
        # TODO: Verify is shared_secret is a good choice
        if is_valid_ip(ip_address) and is_valid_port(port) and len(shared_secret) > 0:
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
        else:
            self.set_response_sensitive(Gtk.ResponseType.OK, False)

    def on_mode_toggled(self, radiobutton, mode):
        if mode == "server":
            self.ip_address_entry.set_placeholder_text("Your IP address")
        elif mode == "client":
            self.ip_address_entry.set_placeholder_text("Server's IP address")

    def get_mode(self):
        if self.server_radiobutton.get_active():
            return vpnprotocol.MODE_SERVER
        elif self.client_radiobutton.get_active():
            return vpnprotocol.MODE_CLIENT

    def get_ip(self):
        return self.ip_address_entry.get_text()

    def get_port(self):
        try:
            return int(self.port_entry.get_text())
        except Exception:
            return None

    def get_ss(self):
        return self.shared_secret_entry.get_text()

    def change_stuff(self):
        box = self.get_content_area()
        box.remove(self.gtk.get_object("setup"))

class TinyVPN():
    """
    """

    def __init__(self):
        """
        """
        self.gladefile = 'main.glade'
        self.gtk = Gtk.Builder()
        self.gtk.add_from_file(self.gladefile)
        self.gtk.connect_signals(self)

        #Objects
        self.SendButton = self.gtk.get_object("SendButton")
        self.MessageEntry = self.gtk.get_object("MessageEntry")
        self.ChatArea = self.gtk.get_object("ChatArea")

        #Signals
        self.SendButton.connect("clicked", self.sendPressed)
        self.MessageEntry.connect("activate", self.sendPressed)

        self.MainWindow = self.gtk.get_object("MainWindow")
        self.MainWindow.connect("delete-event", self.on_MainWindow_delete_event)
        self.MainWindow.show_all()

        self.text_buffer = self.ChatArea.get_buffer()

        #thread = threading.Thread(target=rx_polling, args=(atmega,));
        #thread.daemon = True;
        #thread.start();

        #GLib.idle_add(self.update_tmpx);

        dialog = Setup(self.MainWindow)
        response = dialog.run()
        dialog.hide()

        if response == Gtk.ResponseType.OK:
            self.vpn_connection = vpnprotocol.Connection(dialog.get_ip(), dialog.get_port(), \
                                                dialog.get_ss(), dialog.get_mode(), printmode=False)
        elif response == Gtk.ResponseType.CANCEL:
            print("Ok, still need to figure out how to close everything")

        dialog.destroy()

        self.start_things()

    def start_things(self):
        thread = threading.Thread(target=self.vpn_connection.start, args=());
        thread.daemon = True;
        thread.start();
        GLib.idle_add(self.reading_thread);

    def sendPressed(self, SendButton):
        if (self.vpn_connection.is_connected):
            if (len(self.MessageEntry.get_text()) > 0):
                #Sends message
                message = self.MessageEntry.get_text()

                self.vpn_connection.write_encrypted(bytes(message, 'utf-8'))
                #writes message at the ChatArea
                end_iter = self.text_buffer.get_end_iter()
                self.text_buffer.insert(end_iter, "Me: "+self.MessageEntry.get_text()+"\n")
                #clear textEntry
                self.MessageEntry.set_text("")
        else:
                #writes message at the ChatArea
                end_iter = self.text_buffer.get_end_iter()
                self.text_buffer.insert(end_iter, "**Client not connected**\n")

    #def print_message(self):


    def reading_thread(self):
        self.received_buffer = self.vpn_connection.get_received_buffer()
        if(len(self.received_buffer) != []):
            for element in self.received_buffer:
                #writes message at the ChatArea
                end_iter = self.text_buffer.get_end_iter()
                if(self.vpn_connection.mode == vpnprotocol.MODE_CLIENT):
                    self.text_buffer.insert(end_iter, self.vpn_connection.get_server_ip()+": "+element+"\n")
                    #clear textEntry
                    self.MessageEntry.set_text("")
                elif(self.vpn_connection.mode == vpnprotocol.MODE_SERVER):
                    self.text_buffer.insert(end_iter, self.vpn_connection.get_client_ip()+": "+element+"\n")
                    #clear textEntry
                    self.MessageEntry.set_text("")
        return True

    def on_MainWindow_delete_event(self, widget, event):
        self.clean()
        Gtk.main_quit()

    def clean(self):
        if self.vpn_connection.connected():
            self.vpn_connection.write_encrypted(bytes("f#", 'utf-8'))
            self.vpn_connection.finish()
        else: pass

if __name__ == "__main__":
    try:
        GObject.threads_init();
        t = TinyVPN()
        Gtk.main()

    except KeyboardInterrupt:
        pass
