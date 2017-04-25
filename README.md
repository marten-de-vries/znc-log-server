ZNC Log Server
--------------

A simple web server that shows your ZNC IRC logs, packaged up as a Docker
container.

Volumes:
- mount your log directory as /log in the container

Environment variables
- ``CHANNELS=##PyTest;#SomeOtherChannel``
- ``MOUNT_POINT=/irclogs`` (use / if you want the log viewer at the root of
  your domain)

The container exposes a uWSGI socket at port 3031, which you can easily expose
using e.g. nginx.
