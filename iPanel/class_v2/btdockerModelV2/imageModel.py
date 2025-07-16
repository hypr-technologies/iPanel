# coding: utf-8
# -------------------------------------------------------------------
# Infuze Panel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 Infuze Panel(www.infuze panel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@infuze panel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import os
import json
import traceback

import docker.errors
import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param


class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    # 导出
    def save(self, get):
        """
        :param path 要镜像tar要存放的路径
        :param name 包名
        :param id 镜像
        :param
        :param get:
        :return:
        """

        # 校验参数
        try:
            get.validate([
                Param('path').Require().SafePath(),
                Param('name').Require().String(),
                Param('id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            # if "name" not in get or get.name == "":
            #     return public.return_message(-1, 0, public.lang("Image name cannot be empty"))
            # if "path" not in get or get.path == "":
            #     return public.return_message(-1, 0, public.lang("Mirror path cannot be empty"))
            # if "id" not in get or get.id == "":
            #     return public.return_message(-1, 0, public.lang("Image ID cannot be empty"))

            if "/" in get.name:
                return public.return_message(-1, 0, public.lang("The image name cannot contain /"))

            if "tar" in get.name:
                filename = '{}/{}'.format(get.path, get.name)
            else:
                filename = '{}/{}.tar'.format(get.path, get.name)

            if not os.path.exists(get.path): os.makedirs(get.path)

            public.writeFile(filename, "")
            with open(filename, 'wb') as f:
                image = self.docker_client(self._url).images.get(get.id)
                print(image)
                for chunk in image.save(named=True):
                    f.write(chunk)
            dp.write_log("Image [{}] exported to [{}] successfully".format(get.id, filename))
            return public.return_message(0, 0, public.lang("Successfully saved to:{}", filename))

        except docker.errors.APIError as e:
            if "empty export - not implemented" in str(e):
                return public.return_message(-1, 0, public.lang("Cannot export image!"))
            return public.get_error_info()
        except Exception as e:
            if "Read timed out" in str(e):
                return public.return_message(-1, 0, public.lang("Exporting the image failed and the connection to docker timed out. Please try restarting docker and try again!"))
            return public.return_message(-1, 0, public.lang("Failed to export image!<br> {}", e))

    # 导入
    def load(self, get):
        """
        :param path: 需要导入的镜像路径具体到文件名
        :param get:
        :return:
        """

        # 校验参数
        try:
            get.validate([
                Param('path').Require().SafePath(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            if "path" not in get and get.path == "":
                return public.return_message(-1, 0, public.lang("Please enter the image path!"))

            # 2023/12/20 下午 4:12 判断如果path后缀不为.tar则返回错误
            if not get.path.endswith(".tar"):
                return public.return_message(-1, 0, public.lang("Failed to import the image. The file extension must be.tar!"))

            from btdockerModelV2.dockerSock import image
            sk_image = image.dockerImage()
            sk_image.load_image(get.path)

            dp.write_log("Image [{}] imported successfully!".format(get.path))
            return public.return_message(0, 0, public.lang("Image import was successful!{}", get.path))
        except Exception as e:
            if "Read timed out" in str(e):
                return public.return_message(-1, 0, public.lang("Exporting the image failed and the connection to docker timed out. Please try restarting docker and try again!"))
            if "no such file or directory" in str(e):
                return public.return_message(-1, 0, public.lang("The image import failed and the temporary directory of the container failed to be created. Please check whether the protection software has an interception record!"))
            return public.return_message(-1, 0, public.lang("Failed to import image!<br> {}", e))

    # 列出所有镜像
    def image_list(self, get):
        """
        :param url
        :param get:
        :return:
        """
        try:
            from btdockerModelV2.dockerSock import image
            sk_image = image.dockerImage()
            sk_images_list = sk_image.get_images()

            from btdockerModelV2.dockerSock import container
            sk_container = container.dockerContainer()
            container_list = sk_container.get_container()
            # if not container_list:
            #     return public.return_message(0, 0, data)


            data = list()
            # public.print_log("data000  : {}".format(data))
            # public.print_log("sk_images_镜像列表 sk_images_list: {}".format(sk_images_list))
            for image in sk_images_list:
                # public.print_log("image if111111: {}".format(image))
                # {'Containers': -1, 'Created': 1717026901,
                #  'Id': 'sha256:4f67c83422ec747235357c04556616234e66fc3fa39cb4f40b2d4441ddd8f100',
                #  'Labels': {'maintainer': 'NGINX Docker Maintainers <docker-maint@nginx.com>'}, 'ParentId': '',
                #  'RepoDigests': ['nginx@sha256:0f04e4f646a3f14bf31d8bc8d885b6c951fdcf42589d06845f64d18aec6a3c4d'],
                #  'RepoTags': ['nginx:latest'], 'SharedSize': -1, 'Size': 187667860}
                if image is None:
                    continue

                if image['RepoTags'] is not None and len(image['RepoTags']) != 0:
                    # public.print_log("data2 if111111: {}".format(data))
                    for tag in image['RepoTags']:
                        tmp = {
                            "id": image['Id'],
                            "tags": tag,
                            "name": tag,
                            "digest": image['RepoDigests'][0].split("@")[1] if image['RepoDigests'] else "",
                            "time": image['Created'] if type(image['Created']) == int else None,
                            "size": image['Size'],
                            "created_at": image['Created'],
                            "used": 0,
                            "containers": [],
                        }
                        # public.print_log("tmp tmp tmp: {}".format(tmp))
                        # {'id': 'sha256:4f67c83422ec747235357c04556616234e66fc3fa39cb4f40b2d4441ddd8f100',
                        #  'tags': 'nginx:latest', 'name': 'nginx:latest',
                        #  'digest': 'sha256:0f04e4f646a3f14bf31d8bc8d885b6c951fdcf42589d06845f64d18aec6a3c4d',
                        #  'time': 1717026901, 'size': 187667860, 'created_at': 1717026901, 'used': 0, 'containers': []}
                        # public.print_log("container_list   if: {}".format(container_list))
                        self.structure_images_list(container_list, tmp)
                        # public.print_log("data jhshs哈666666 if: {}".format(data))
                        data.append(tmp)
                        # public.print_log("data2 if: {}".format(data))
                else:
                    # public.print_log("data2 if: {}".format(data))
                    tmp = {
                        "id": image['Id'],
                        "tags": "<none>",
                        "name": "<none>",
                        "digest": image['RepoDigests'][0].split("@")[1] if image['RepoDigests'] else "",
                        "time": image['Created'] if type(image['Created']) == int else None,
                        "size": image['Size'],
                        "created_at": image['Created'],
                        "used": 0,
                        "containers": [],
                    }

                    self.structure_images_list(container_list, tmp)
                    # public.print_log("data2333 if: {}".format(data))
                    data.append(tmp)
                    # public.print_log("data2 else : {}".format(data))


            # public.print_log("data2kjefa : {}".format(type(data)))
            return public.return_message(0, 0, data)
        except Exception as ex:
            import traceback
            # public.print_log("尺码个| info: {}".format(ex))
            public.print_log(traceback.format_exc())
            return public.return_message(0, 0, data)

    def structure_images_list(self, container_list, image_info):
        '''
            @name
            @author wzz <2024/5/22 下午5:53>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            for container in container_list:
                if image_info['id'] in container['ImageID']:
                    image_info['used'] = 1
                    image_info['containers'].append({
                        "container_id": container['Id'],
                        "container_name": dp.rename(container['Names'][0].replace("/", "")),
                    })
        except:
            pass


    def get_image_attr(self, images):
        image = images.list()
        return [i.attrs for i in image]

    def get_logs(self, get):
        # 校验参数
        try:
            get.validate([
                Param('logs_file').Require().SafePath(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import files
        logs_file = get.logs_file
        return public.return_message(0, 0, files.files().GetLastLine(logs_file, 20))

    # 构建镜像
    def build(self, get):
        """
        :param path         dockerfile dir
        :param pull         如果引用的镜像有更新自动拉取
        :param tag          标签 jose:v1
        :param data         在线编辑配置
        :param get:
        :return:
        """

        # # 校验参数
        # try:
        #     get.validate([
        #         Param('path').Require().SafePath(),
        #     ], [
        #         public.validate.trim_filter(),
        #     ])
        # except Exception as ex:
        #     public.print_log("error info: {}".format(ex))
        #     return public.return_message(-1, 0, str(ex))

        public.writeFile(self._log_path, "Start building the image!")
        if not hasattr(get, "pull"):
            get.pull = False

        min_time = None
        if hasattr(get, "data") and get.data:
            min_time = public.format_date("%Y%m%d%H%M")
            get.path = "/tmp/{}/Dockerfile".format(min_time)
            os.makedirs("/tmp/{}".format(min_time), exist_ok=True)
            public.writeFile(get.path, get.data)

        if not os.path.exists(get.path):
            return public.return_message(-1, 0, public.lang("Please enter the correct DockerFile path!"))

        try:
            # 2024/1/18 下午 12:05 取get.path的目录
            get.path = os.path.dirname(get.path)
            image_obj, generator = self.docker_client(self._url).images.build(
                path=get.path,
                pull=True if get.pull == "1" else False,
                tag=get.tag,
                forcerm=True
            )

            if min_time is not None:
                public.ExecShell("rm -rf {}".format(get.path))

            dp.log_docker(generator, "Docker Build tasks!")
            dp.write_log("Build image [{}] successful!".format(get.tag))
            return public.return_message(0, 0, public.lang("Build image successfully!"))
        except docker.errors.BuildError as e:
            if "TLS handshake timeout" in str(e):
                return public.return_message(-1, 0, public.lang("Build failed, connection timed out"))
            return public.return_message(-1, 0, public.lang("Build failed! {}", e))
        except docker.errors.APIError as e:
            if "Cannot locate specified Dockerfile" in str(e):
                return public.return_message(-1, 0, public.lang("Build failed!The specified Dockerfile was not found"))
            return public.return_message(-1, 0, public.lang("Build failed!{}", e))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Build failed!{}", e))

    # 删除镜像
    def remove(self, get):
        """
        :param url
        :param id  镜像id
        :param name 镜像tag
        :force 0/1 强制删除镜像
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('force').Require().Integer(),
                Param('name').Require().String(),
                Param('id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            from btdockerModelV2.dockerSock import image
            sk_image = image.dockerImage()
            image_inspect = sk_image.inspect(get.name)
            if not image_inspect:
                self.docker_client(self._url).images.remove(get.id)
            else:
                self.docker_client(self._url).images.remove(get.name)

            dp.write_log("Deletion of image【{}】successful!".format(get.name))
            return public.return_message(0, 0, public.lang("Mirror deleted successfully!"))

        except docker.errors.ImageNotFound as e:
            return public.return_message(-1, 0, public.lang("The delete failed and the image may not exist!"))

        except docker.errors.APIError as e:
            if "image is referenced in multiple repositories" in str(e):
                return public.return_message(-1, 0, public.lang("The image ID is used in more than one image, force the image to be deleted!"))
            if ("using its referenced image" in str(e) or
                    "image is being used by stopped container" in str(e) or
                    "image is being used by running container" in str(e)):
                return public.return_message(-1, 0, public.lang("The image is in use. Please delete the container before deleting the image!"))

            return public.return_message(-1, 0, public.lang("Failed to delete image!<br> {}", e))
        except Exception as e:
            if "Read timed out" in str(e):
                return public.return_message(-1, 0, public.lang("Failed to delete image,The connection to docker timed out, please restart and try again!"))
            return public.return_message(-1, 0, public.lang("Failed to delete image!<br> {}", e))

    # 拉取指定仓库镜像
    def pull_from_some_registry(self, get):
        """
        :param name 仓库名11
        :param url
        :param image
        :param get:
        :return:
        """
        if not hasattr(get, "_ws"):
            return True

        from btdockerModelV2 import registryModel as dr

        # try:
            # if get.name == "Docker public repository":
            #     login = dr.main().login(self._url, "docker.io", None, None)['status']
            #     if not login:
            #         get._ws.send(
            #             "bt_failed, Login to the repository [docker.io] failed, please try to log in to this repository again!\r\n")
            #         return login

        r_info = {
            "name": "Docker public repository",
            "reg_name": "Docker public repository",
            "url": "docker.io",
            "username": None,
            "password": None,
            "namespace": "library"
        }
        try:
            if get.name != "Docker public repository":
                r_info = dr.main().registry_info(get)
                r_info['username'] = public.aes_decrypt(r_info['username'], self.aes_key)
                r_info['password'] = public.aes_decrypt(r_info['password'], self.aes_key)
                login = dr.main().login(self._url, r_info['url'], r_info['username'], r_info['password'])['status']
                if not login:
                    get._ws.send("failed," + public.lang("{}\r\n",login['msg']))
                    return login
        except Exception as e:
            get._ws.send(
                public.lang("failed, Login to repository [{}] failed, please try to log in to this repository again!\r\n",get.name))
            return public.return_message(-1, 0, public.lang("bt_failed, Login to repository [{}] failed, please try to log in to this repository again! {}",get.name, e))

        get.username = r_info['username']
        get.password = r_info['password']
        get.registry = r_info['url']
        get.namespace = r_info['namespace']
        get.name = r_info['reg_name'] if "reg_name" in r_info and r_info["reg_name"] != "" else r_info["name"]

        return self.pull(get)

    # 推送镜像到指定仓库
    def push(self, get):
        """
        :param id       镜像ID
        :param url      连接docker的url
        :param tag      标签 镜像名+版本号v1
        :param name     仓库名
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('tag').Require().String(),
                Param('name').Require().String(),
                Param('id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if "/" in get.tag:
            return public.return_message(-1, 0, public.lang("The pushed image cannot contain [/], please use the following  format: image:v1 (image name: version)"))
        if ":" not in get.tag:
            get.tag = "{}:latest".format(get.tag)

        public.writeFile(self._log_path, "Start pushing the image!\n")

        from btdockerModelV2 import registryModel as dr
        r_info = dr.main().registry_info(get.name)
        r_info['username'] = public.aes_decrypt(r_info['username'], self.aes_key)
        r_info['password'] = public.aes_decrypt(r_info['password'], self.aes_key)

        if get.name == "docker official" and r_info['url'] == "docker.io":
            public.writeFile(self._log_path, "The image cannot be pushed to the Docker public repository!\n")
            return public.return_message(-1, 0, public.lang("Unable to push to Docker public repository!"))

        try:
            login = dr.main().login(self._url, r_info['url'], r_info['username'], r_info['password'])['status']
            if not login:
                return public.return_message(-1, 0, public.lang("Repository [{}] Login failed!", r_info['url']))

            auth_conf = {
                "username": r_info['username'],
                "password": r_info['password'],
                "registry": r_info['url']
            }
            # repository       namespace/image

            repository = r_info['url']
            reg_name = r_info['reg_name'] if "reg_name" in r_info and r_info["reg_name"] != "" else r_info["name"]
            image = "{}/{}/{}:{}".format(repository, r_info['namespace'], reg_name, get.tag)

            self.tag(self._url, get.id, image)
            ret = self.docker_client(self._url).images.push(
                repository=image.split(":")[0],
                tag=image.split(":")[1],
                auth_config=auth_conf,
                stream=True
            )

            dp.log_docker(ret, "Image push task")
            # 删除自动打标签的镜像
            get.name = image
            self.remove(get)

        except docker.errors.APIError as e:
            if "invalid reference format" in str(e):
                return public.return_message(-1, 0, public.lang("Push failed, image label error, please enter such as: v1.0.1"))
            if "denied: requested access to the resource is denied" in str(e):
                return public.return_message(-1, 0, public.lang("Push failed, do not have permission to push to this repository!"))
            return public.return_message(-1, 0, public.lang("Push failure!{}", e))

        dp.write_log("Image [{}] pushed successfully!".format(image))
        return public.return_message(0, 0, public.lang("Push successfully, mirror:{}", image))

    def tag(self, url, image_id, tag):
        """
        为镜像打标签
        :param repository   仓库namespace/images
        :param image_id:          镜像ID
        :param tag:         镜像标签jose:v1
        :return:
        """
        image = tag.split(":")[0]
        tag_ver = tag.split(":")[1]
        self.docker_client(url).images.get(image_id).tag(
            repository=image,
            tag=tag_ver
        )
        return public.return_message(0, 0, public.lang("Successfully set!"))

    def pull(self, get):
        """
        :param image
        :param url
        :param registry
        :param username 拉取私有镜像时填写 1
        :param password 拉取私有镜像时填写
        :param get:
        :return:
        """

        # try:
        get._ws.send(public.lang("Pulling the image, please wait...\r\n"))
        import docker.errors
        import time
        time.sleep(0.1)
        # get._ws.send(public.lang("Pull or search for images...\r\n"))
        try:
            auth_data = {
                "username": get.username,
                "password": get.password,
                "registry": get.registry if get.registry else None
            }
            auth_conf = auth_data if get.username else None

            if get.registry == "docker.io":
                get.image = '{}:latest'.format(get.image) if ':' not in get.image else get.image

            if not hasattr(get, "tag"): get.tag = get.image.split(":")[-1]

            if get.registry != "docker.io":
                get.image = "{}/{}/{}:{}".format(get.registry, get.namespace, get.name, get.image)

            ret = dp.docker_client_low(self._url).pull(
                repository=get.image.split(":")[0],
                auth_config=auth_conf,
                tag=get.tag,
                stream=True
            )

            if not ret:
                get._ws.send("failed," + public.lang("pull failed!\r\n"))
                return
            last_result = None
            last_progress_str = None
            while True:
                try:
                    output = next(ret)
                    output = json.loads(output)
                    if "errorDetail" in output:
                        if "message" in output['errorDetail']:
                            if ("download failed after" in output['errorDetail']['message'] and
                                    "i/o timeout" in output['errorDetail']['message']):
                                try:
                                    if not os.path.exists("/www/server/panel/config/docker_registry.json"):
                                        public.DownloadFile(
                                            "{}/src/docker_registry.json".format(public.get_url()),
                                            "/www/server/panel/config/docker_registry.json"
                                        )

                                    registry_list = json.loads(
                                        public.readFile("/www/server/panel/config/docker_registry.json"))
                                    if len(registry_list) > 0:
                                        get._ws.send(
                                            public.lang("Failed to use the default mirror station to pull the image! Trying to use another mirror station to pull for you, please wait...\r\n"))
                                        if not "/" in get.image:
                                            get.image = "{}/library/{}".format(registry_list[0].replace("https://", ""),
                                                                               get.image)
                                        else:
                                            get.image = "{}/{}".format(registry_list[0].replace("https://", ""),
                                                                       get.image)

                                        stdout, stderr = public.ExecShell("docker pull {}".format(get.image))
                                        if stderr:
                                            get._ws.send("failed," + public.lang("Failed to pull image!\r\n"))
                                            return public.return_message(-1, 0, public.lang("Failed to pull the image!"))

                                        public.ExecShell("docker tag {} {}".format(get.image, get.image.split("/")[-1]))
                                        public.ExecShell("docker rmi {}".format(get.image))
                                        public.writeFile("/www/server/panel/config/bad_registry.pl", registry_list[0])
                                        get._ws.send(
                                            "successful," + public.lang( "Image pull [{}] successful, it is recommended to set: {} as the acceleration station\r\n",get.image, registry_list[0])
                                        )
                                except:
                                    import traceback
                                    print(traceback.format_exc())
                                    pass
                        else:
                            get._ws.send("failed," + public.lang("Pull failed!{}\r\n",output['errorDetail']))

                        return

                    if 'status' in output:
                        output_str = output['status']
                        if output_str == "Downloading":
                            progress = output['progressDetail']
                            if not progress: continue
                            current_mb = progress['current'] / (1024 * 1024)  # 将当前字节数转换为兆字节
                            total_mb = progress['total'] / (1024 * 1024)  # 将总字节数转换为兆字节
                            progress_str = "Downloading: {:.2f}MB/{:.2f}MB, {}%".format(current_mb, total_mb, int(
                                progress['current'] * 100 / progress['total']))
                            if progress_str != last_progress_str:
                                get._ws.send(progress_str + "\r\n")
                                last_progress_str = progress_str
                        else:
                            if output_str != last_result:
                                get._ws.send(output_str + "\r\n")
                                last_result = output_str
                    time.sleep(0.1)
                except StopIteration:
                    get._ws.send("successful," +public.lang("Image pull [{}] successful\r\n",get.image))
                    return public.return_message(0, 0, public.lang("Image pulled successfully!"))
                except ValueError:
                    get._ws.send("failed," + public.lang("Failed to pull image!\r\n"))
                    return public.return_message(-1, 0, public.lang("Failed to pull image!"))

        except docker.errors.ImageNotFound as e:
            if "pull access denied for" in str(e):
                get._ws.send(
                    "failed," + public.lang("Pull failed,The image does not exist, or the image may be a private image. You need to enter your dockerhub account password!\r\n"))
                return
            get._ws.send("failed," + public.lang("pull failed!{}\r\n",e))
            return

        except docker.errors.NotFound as e:
            if "not found: manifest unknown" in str(e):
                get._ws.send("failed," + public.lang("pull failed,There is no such image in the repository!\r\n"))
                return
            get._ws.send("failed," + public.lang("pull failed!{}\r\n",e))
            return

        except docker.errors.APIError as e:
            if "invalid tag format" in str(e):
                get._ws.send("failed," + public.lang("pull failed, The image format is wrong, such as: nginx:v 1!\r\n"))
                return
            get._ws.send("failed," + public.lang("pull failed!{}\r\n",e))
            return

        # except Exception as e:
        #    # public.print_log("拉取镜像  -- {}".format(e))
        #    public.print_log(traceback.format_exc())

    # 拉取镜像
    def pull_high_api(self, get):
        """
        :param image
        :param url
        :param registry
        :param username 拉取私有镜像时填写
        :param password 拉取私有镜像时填写
        :param get:
        :return:
        """
        import docker.errors
        try:
            if ':' not in get.image:
                get.image = '{}:latest'.format(get.image)
            auth_data = {
                "username": get.username,
                "password": get.password,
                "registry": get.registry if get.registry else None
            }

            auth_conf = auth_data if get.username else None

            if get.registry != "docker.io":
                get.image = "{}/{}/{}".format(get.registry, get.namespace, get.image)

            ret = self.docker_client(get.url).images.pull(repository=get.image, auth_config=auth_conf)
            if ret:
                return public.return_message(0, 0, public.lang("The image was pulled successfully."))
            else:
                return public.return_message(-1, 0, public.lang("There may not be this mirror image."))

        except docker.errors.ImageNotFound as e:
            if "pull access denied for" in str(e):
                return public.return_message(-1, 0, public.lang("Failed to pull the image, this is a private image, please enter the account password!"))
            return public.return_message(-1, 0, public.lang("Pull image failure <br><br> Reason: {}", e))

    def image_for_host(self, get):
        """
        获取镜像大小和获取镜像数量
        :param get:
        :return:
        """
        res = self.image_list(get)
        if res['status'] == -1: return res

        num = len(res['message']['images_list'])
        size = 0

        for i in res['message']['images_list']:
            size += i['size']
        return public.return_message(0, 0, {'num': num, 'size': size})

    def prune(self, get):
        """
        删除无用的镜像
        :param get:
        :return:
        """
        dang_ling = True if "filters" in get and get.filters == "0" else False

        try:
            res = self.docker_client(self._url).images.prune(filters={'dangling': dang_ling})

            if not res['ImagesDeleted']:
                return public.return_message(0, 0, public.lang("No useless images!"))

            dp.write_log("Delete useless image successfully!")
            return public.return_message(0, 0, public.lang("successfully delete!"))

        except docker.errors.APIError as e:
            return public.return_message(-1, 0, public.lang("failed to delete!{}", e))
        except Exception as e:
            if str(e).find("Read timed out") != -1:
                return public.return_message(-1, 0,
                                             public.lang("Deletion of useless images failed and the connection to docker timed out. Please try restarting the docker service and try again!"))
            return public.return_message(-1, 0, public.lang("failed to delete!{}", e))
    # 2024/5/17 下午6:30 构造返回结果
    def structure_result(self, results, sk_images_list):
        '''
            @name
            @author wzz <2024/5/17 下午6:30>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        for r in results:
            # public.print_log("is_pullvis_pull    {}".format(r))
            r["is_pull"] = 0
            r['id'] = ""
            for image in sk_images_list:
                if image is None: continue
                i_RepoTags = image['RepoTags'][0] if not image['RepoTags'] is None and len(
                    image['RepoTags']) != 0 else "<none>"
                if i_RepoTags == "<none>": continue
                if r['name'] in i_RepoTags and i_RepoTags == "{}:latest".format(r['name']):
                    r["is_pull"] = 1
                    r['id'] = image['Id']

        return sorted(results, key=lambda x: x['star_count'], reverse=True)

    # 2023/12/13 上午 11:08 镜像搜索 todo 关键字查询调用ws接口 暂时没查到
    def search(self, get):
        '''
            @name 镜像搜索,docker hub官方镜像列表
                从docker hub官方镜像列表获取最新排序镜像
                数据库在/www/server/panel/class_v2/btdockerModelV2/config/docker_hub_repos.db
                每隔1个月从官网同步一次
                脚本在/www/server/panel/class_v2/btdockerModelV2/script/syncreposdb.py
            @author wzz <2023/12/13 下午 3:41>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        try:
            get.name = get.get("name/s", "")
            from btdockerModelV2.dockerSock import image
            sk_image = image.dockerImage()
            sk_images_list = sk_image.get_images()

            if get.name == "":
                # 2024/3/20 上午 10:10 如果get.name是空,则返回docker_hub_repos.db中results表的所有镜像
                import db, os

                sql = db.Sql()
                sql.dbfile('{}/class_v2/btdockerModelV2/config/docker_hub_repos.db'.format(public.get_panel_path()))
                # 2024/3/20 上午 10:24 按照star_count排序
                results = sql.table('results').field('name,description,star_count,is_official').order('star_count desc').select()
                if not results or results == [] :
                    return public.return_message(0, 0, [])

                return public.return_message(0, 0, self.structure_result(results, sk_images_list))

            search_result = sk_image.search(get.name)
            if not search_result or search_result == []:
                return public.return_message(0, 0, [])

            return public.return_message(0, 0, self.structure_result(search_result, sk_images_list))
        except Exception as e:
            # if os.path.exists('data/debug.pl'):
            #     print(public.get_error_info())
            public.print_log(public.get_error_info())
            return public.return_message(-1, 0, [])

    # 拉取容器日志
    def get_cmd_log(self, get):
        """
        拉取容器日志
        @param get:
        @return:
        """
        get.wsLogTitle = "Start executing the command, please wait..."
        get._log_path = self._rCmd_log
        return self.get_ws_log(get)
