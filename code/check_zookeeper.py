# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import os
import BaseHTTPServer
import SimpleHTTPServer
import SocketServer

from register_file import RegisterFile
from register_util import RegisterUtil


################################################################################
# class: threading server
################################################################################
class SimpleThreadingServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


################################################################################
# class: request handler
################################################################################
class ZookeeperRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    my_basedir = os.path.dirname(os.path.realpath(__file__)).replace('/bin', '')
    my_util = RegisterUtil("register_zookeeper", "{}/log".format(my_basedir))

    check_output = ""
    check_iid = ""
    check_message = ""

    def _set_headers(self):
        command1 = "echo ruok | nc localhost 2181"
        command2 = "curl -s http://169.254.169.254/latest/meta-data/instance-id"
        self.check_output = self.my_util.exec_shell_command(command1, enable_logging=False)
        self.check_iid = self.my_util.exec_shell_command(command2, enable_logging=False)
        self.check_message = "{} {}".format(self.check_output, self.check_iid)

        if self.check_output == "imok":
            self.my_util.log.info("check_zookeeper: [200] {}".format(self.check_message))
            self.send_response(200)
        else:
            self.my_util.log.error("check_zookeeper: [500] {}".format(self.check_message))
            self.send_response(500)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(self.check_message))
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(self.check_message)

    def do_HEAD(self):
        self._set_headers()
        self.wfile.write(self.check_message)


################################################################################
# functions: main
################################################################################
def main():
    my_basedir = os.path.dirname(os.path.realpath(__file__)).replace('/bin', '')
    my_util = RegisterUtil("service_check_zookeeper", "{}/log".format(my_basedir))
    my_region = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\\" '{print $4}'")
    my_file = RegisterFile(my_util, my_region, my_basedir)
    params = my_file.process_conf("{}/etc/register_zookeeper.conf".format(my_basedir))
    http_ip = '0.0.0.0'
    if 'check_zookeeper_port' in params:
        http_port = int(params['check_zookeeper_port'])
    else:
        http_port = 2180
    http_handler = ZookeeperRequestHandler
    my_util.log.info("Starting server at {}:{}".format(http_ip, http_port))
    # httpd = SocketServer.TCPServer((http_ip, http_port), http_handler)
    httpd = SimpleThreadingServer((http_ip, http_port), http_handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
