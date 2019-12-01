from jinja2 import Environment, FileSystemLoader
import os
import argparse
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import threading
import http.server
import socketserver
import pdb


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return



class Logger:
    def __init__(self, log_dir=None, clear=False):
        if log_dir is not None:
            self.log_dir = log_dir
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)
            self.log_dir = log_dir
            self.plot_dir = os.path.join(log_dir, "plot")
            if not os.path.exists(self.plot_dir):
                os.mkdir(self.plot_dir)
            elif clear:
                os.system("rm {}/plot/*".format(log_dir))
            self.image_dir = os.path.join(log_dir, "image")
            if not os.path.exists(self.image_dir):
                os.mkdir(self.image_dir)
            elif clear:
                os.system("rm -rf {}/image/*".format(log_dir))
            if not os.path.exists(os.path.join(log_dir, "image_ticks")):
                os.mkdir(os.path.join(log_dir, "image_ticks"))
            elif clear:
                os.system("rm -rf {}/image_ticks/*".format(log_dir))
            self.plot_vals = {}
            self.plot_times = {}
            PORT = 8000
            def http_server():
                Handler = QuietHandler
                with socketserver.TCPServer(("", PORT), Handler) as httpd:
                    #print("serving at port", PORT)
                    httpd.serve_forever()
            x=threading.Thread(target=http_server)
            x.start()
            print("==============================================")
            print("visualize at http://host ip:{}/{}.html".format(PORT, self.log_dir))
            print("==============================================")


    def add_scalar(self, name, value, t_iter):
        if not name in self.plot_vals:
            self.plot_vals[name] = [value]
            self.plot_times[name] = [t_iter]
        else:
            self.plot_vals[name].append(value)
            self.plot_times[name].append(t_iter)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.plot_times[name], self.plot_vals[name])
        fig.savefig(os.path.join(self.plot_dir, '%s.png'%name))
        plt.close()
    #add_image('image', torchvision.utils.make_grid(img), num_iter)

    def add_image(self, name, image, t_iter):
       path_name = os.path.join(self.image_dir, name)
       if not os.path.exists(path_name):
           os.mkdir(path_name)
       image = image.detach().cpu().numpy()
       image = image.transpose((1, 2, 0))
       image = Image.fromarray((image*255).astype(np.uint8))
       image.save(os.path.join(path_name, "%d.png"%t_iter))
       with open(os.path.join(self.log_dir, "image_ticks", name+".txt"), "a") as f:
           f.write(str(t_iter)+'\n')

    def write_html_eval(self, base_dir):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(os.path.join(dir_path, "templates"))
        env = Environment(loader=file_loader)
        template = env.get_template('val.html')

        list_exp_ticks = []
        list_exp_paths = []
        list_img_names = []
        list_dirs = os.listdir(base_dir)
        if "mask" in list_dirs:
            list_dirs.remove("mask")
        list_dirs = sorted(list_dirs)
        list_dirs = ["mask"] + list_dirs
        k=0
        for i, exp in enumerate(list_dirs):
            if os.path.isdir(os.path.join(base_dir, exp)) and not exp.startswith("."):
                list_exp_paths.append( os.path.join(exp, "image"))
                list_exp_ticks.append( os.listdir(os.path.join(base_dir, exp, "image")))
                if k == 0:
                    _l = list(filter(lambda x: not x.startswith("."), list_exp_ticks[0]))
                    list_img_names += \
                            os.listdir(
                                os.path.join(base_dir, exp, "image", str(_l[0]))
                                )
                    k += 1
        output = template.render( list_exp_ticks=list_exp_ticks, list_exp_paths=list_exp_paths, list_img_names=list_img_names)
        #print(output)
        with open("{}/validation.html".format(base_dir), "w") as f:
            f.writelines(output)

    def write_html(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(os.path.join(dir_path, "templates"))
        env = Environment(loader=file_loader)
        template = env.get_template('train.html')

        prefix = self.log_dir
        re_prefix = self.log_dir.split("/")[-1]
        plotpath = os.path.join(prefix, "plot")
        plotfiles = os.listdir(plotpath)
        plotfiles = list(map(lambda x: os.path.join(re_prefix, "plot", x), plotfiles))

        image_tick_path = []
        imagepath = os.path.join(prefix, "image")
        for folder in os.listdir(imagepath):
            ticks = open("{}/image_ticks/{}.txt".format(prefix, folder), "r").read()
            ticks = ticks.split('\n')[:-1]
            ticks = list(map(lambda x:int(x), ticks))
            folderpath = os.path.join(re_prefix, "image", folder)
            image_tick_path.append({"tick":ticks, "path":folderpath})

        output = template.render( plotfiles=plotfiles, image_tick_path=image_tick_path, title_name=prefix)
        #print(output)
        with open("{}.html".format(prefix), "w") as f:
            f.writelines(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Videos to images')
    parser.add_argument('--log_dir', type=str, help='log dir')
    parser.add_argument('--log_dir_eval', type=str, help='log dir')
    args = parser.parse_args()
    logger = Logger(args.log_dir)
    #logger.write_html()
    logger.write_html_eval(args.log_dir_eval)
