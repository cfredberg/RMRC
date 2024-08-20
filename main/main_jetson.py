import server.app
import master_process_util as mutil

import multiprocessing

if __name__ == '__main__':
    server_process = mutil.create_process(server.app.process, (), "server")

    server_process.join()