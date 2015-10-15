from gi.repository import Gtk, GdkPixbuf, GObject, GLib

class Chat():
    """
    """

    def __init__(self):
        """
        """
        self.gladefile = 'chat.glade'
        self.gtk = Gtk.Builder()
        self.gtk.add_from_file(self.gladefile)
        self.gtk.connect_signals(self)

        self.MainWindow = self.gtk.get_object("MainWindow")
        self.MainWindow.connect("delete-event", self.on_MainWindow_delete_event)
        self.MainWindow.show_all()

        #thread = threading.Thread(target=rx_polling, args=(atmega,));
        #thread.daemon = True;
        #thread.start();

        #GLib.idle_add(self.update_tmpx);

    def on_MainWindow_delete_event(self, widget, event):
        self.clean()
        Gtk.main_quit()

    def clean(self):
        pass;


if __name__ == "__main__":
    try:
        GObject.threads_init();
        c = Chat()
        Gtk.main()

    except KeyboardInterrupt:
        pass
