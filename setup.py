from gi.repository import Gtk, GdkPixbuf, GObject, GLib

class Setup(Gtk.Assistant):
    """
    """

    def __init__(self):
        """
        """
        self.gladefile = 'setup.glade'
        self.gtk = Gtk.Builder()
        self.gtk.add_from_file(self.gladefile)
        self.gtk.connect_signals(self)

        self.assistant = self.gtk.get_object("Setup")
        self.assistant.connect("delete-event", self.on_MainWindow_delete_event)
        self.assistant.show_all()

        self.box1  = self.gtk.get_object('box1');

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
        s = Setup()
        Gtk.main()

    except KeyboardInterrupt:
        pass
