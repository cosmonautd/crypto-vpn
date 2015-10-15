from gi.repository import Gtk, GdkPixbuf, GObject, GLib

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
        self.show_all()

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

        self.MainWindow = self.gtk.get_object("MainWindow")
        self.MainWindow.connect("delete-event", self.on_MainWindow_delete_event)
        self.MainWindow.show_all()

        #thread = threading.Thread(target=rx_polling, args=(atmega,));
        #thread.daemon = True;
        #thread.start();

        #GLib.idle_add(self.update_tmpx);

        """dialog = Setup(self.MainWindow)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("The OK button was clicked")
        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        dialog.destroy()"""

    def on_MainWindow_delete_event(self, widget, event):
        self.clean()
        Gtk.main_quit()

    def clean(self):
        pass;


if __name__ == "__main__":
    try:
        GObject.threads_init();
        t = TinyVPN()
        Gtk.main()

    except KeyboardInterrupt:
        pass
