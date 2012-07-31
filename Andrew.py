import sublime
import sublime_plugin
import subprocess
import os
import fnmatch
import re
import threading


class NewAndroidProjectCommand(sublime_plugin.WindowCommand):
    version = ""
    package = ""
    activity = ""
    foldername = ""
    versions = []
    versionsHeaders = []

    def run(self):
        self.window.show_input_panel("Application Name:", "", self.on_done1, None, None)

    def on_done1(self, text):
        self.activity = text
        versionsHeaders = self.get_android_versions()
        self.window.show_quick_panel(versionsHeaders, self.on_done2)

    def on_done2(self, index):
        if(index == -1):
            return
        self.version = self.versions[index]
        self.window.show_input_panel("Android Package:", "com.", self.on_done3, None, None)

    def on_done3(self, text):
        self.package = text
        settings = sublime.load_settings('Andrew.sublime-settings')
        self.window.show_input_panel("Path to project:", settings.get('workspace') + self.activity + "/", self.on_done4, None, None)

    def on_done4(self, text):
        self.foldername = text
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + "tools/android create project --target " + self.version + " --path " + self.foldername + " --activity " + self.activity + " --package " + self.package
        p = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if p.stdout is not None:
            msg = p.stdout.readline()
            print msg
        self.window.open_file(self.foldername + "AndroidManifest.xml")
        os.chdir(self.foldername)
        self.window.run_command("save_project_as")
        self.window.run_command("prompt_add_folder")

    def get_android_versions(self):
        self.versionsHeaders = []
        self.versions = []
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + 'tools/android list | grep -A 1 "android-"'
        p = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if p.stdout is not None:
            msg = p.stdout.readlines()
            while len(msg) > 1:
                row1 = msg.pop()
                row2 = msg.pop()
                if(len(msg) > 0):
                    msg.pop()
                m1 = re.search('[\ ]*Name: ([a-zA-Z0-9\ \.]*)', row1)
                m2 = re.search('(android-[0-9] + )', row2)
                name = m1.group(1)
                version = m2.group(1)
                self.versions.append(version)
                self.versionsHeaders.append([name, version])
        return self.versionsHeaders


class CallAdbCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + "/platform-tools/adb devices"
        subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


class OpenSdkCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + "/tools/android sdk"
        subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


class OpenDevicesCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + "/tools/android avd"
        subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


class OpenDdmsCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        cmd_a = settings.get('android_sdk_path') + "/tools/ddms"
        subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


class LocateSdkCommand(sublime_plugin.WindowCommand):
    def run(self):
        options = [
            ["Search SDK Automatically", "It may take a few minutes."],
            ["Set SDK Path Manually", "Write down the root path of your android SDK"]
        ]
        self.window.show_quick_panel(options, self.on_done)

    def on_done(self, index):
        if index == 0:
            self.auto_search()
        elif index == 1:
            self.manual_input()

    def auto_search(self):
        cmd_a = "find / -name apkbuilder -print0 2>/dev/null | grep -FzZ -m 1 tools/apkbuilder"
        p = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=None, shell=True)
        if p.stdout is not None:
            msg = p.stdout.readline()
            msg = msg.rstrip(' \t\r\n\0').replace('tools/apkbuilder', '')
        self.window.show_input_panel("Android SDK Path:", msg, self.on_done2, None, None)

    def manual_input(self):
        settings = sublime.load_settings("Andrew.sublime-settings")
        self.window.show_input_panel("Android SDK Path:", settings.get("android_sdk_path", "/"), self.on_done2, None, None)

    def on_done2(self, text):
        settings = sublime.load_settings('Andrew.sublime-settings')
        settings.set('android_sdk_path', text)
        sublime.save_settings('Andrew.sublime-settings')


class WorkspacePathCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        path = settings.get("workspace", "~/workspace/")
        self.window.show_input_panel("Workspace Path:", path, self.on_done, None, None)

    def on_done(self, text):
        settings = sublime.load_settings('Andrew.sublime-settings')
        settings.set('workspace', text)
        sublime.save_settings('Andrew.sublime-settings')


class PathDependantCommands(sublime_plugin.WindowCommand):
    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path


class CompileDebugCommand(PathDependantCommands):
    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml
                p = subprocess.Popen("ant debug", cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p.stdout is not None:
                    msg = p.stdout.readlines()
                    for line in msg:
                        print line


class CompileReleaseCommand(PathDependantCommands):
    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml
                p = subprocess.Popen("ant release", cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p.stdout is not None:
                    msg = p.stdout.readline()
                    print msg


class CleanProjectCommand(PathDependantCommands):
    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml
                p = subprocess.Popen("ant clean", cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p.stdout is not None:
                    msg = p.stdout.readlines()
                    for line in msg:
                        print line


class LayoutSnippetsCommand(sublime_plugin.TextCommand):

    snippets = [
                    "absolutelayout",
                    "edittext"
                    "imagebutton"
                    "imageview"
                    "linearlayout",
                    "listview",
                    "relativelayout",
                    "switch",
                    "textview",
                    "togglebutton",
                    "view"
                ]
    snippetsHeaders = [
                            "AbsoluteLayout",
                            "EditText",
                            "ImageButton",
                            "ImageView",
                            "LinearLayout",
                            "ListView",
                            "RelativeLayout",
                            "Switch",
                            "TextView",
                            "ToggleButton",
                            "View"
                        ]

    def run(self, text):
        self.view.window().show_quick_panel(self.snippetsHeaders, self.on_done, sublime.MONOSPACE_FONT)
        return

    def on_done(self, index):
        if index < 0:
            return
        snippet = self.snippets[index]
        self.view.run_command('insert_snippet', {"name": "Packages/Andrew/snippets/" + snippet + ".sublime-snippet"})


class ResourcesCommand(sublime_plugin.TextCommand):

    resourcesLayout = []
    resourcesDrawable = []
    resourcesId = []
    resourcesString = []
    edit = 0

    def run(self, edit):
        options = [
            "Layout",
            "Drawable",
            "Id",
            "String"
        ]
        self.edit = edit
        self.view.window().show_quick_panel(options, self.on_done)

    def on_done(self, index):
        self.loadLayouts()
        self.loadDrawables()
        self.loadIds()
        self.loadStrings()
        if index == 0:
            self.view.window().show_quick_panel(self.resourcesLayout, self.on_done_layout)
        elif index == 1:
            self.view.window().show_quick_panel(self.resourcesDrawable, self.on_done_drawable)
        elif index == 2:
            self.view.window().show_quick_panel(self.resourcesId, self.on_done_id)
        elif index == 3:
            self.view.window().show_quick_panel(self.resourcesString, self.on_done_string)

    def on_done_layout(self, index):
        if index is not -1:
            self.view.insert(self.edit, self.view.sel()[0].begin(), "R.layout." + self.resourcesLayout[index])

    def on_done_drawable(self, index):
        if index is not -1:
            self.view.insert(self.edit, self.view.sel()[0].begin(), "R.drawable." + self.resourcesDrawable[index])

    def on_done_id(self, index):
        if index is not -1:
            self.view.insert(self.edit, self.view.sel()[0].begin(), "R.id." + self.resourcesId[index])

    def on_done_string(self, index):
        if index is not -1:
            self.view.insert(self.edit, self.view.sel()[0].begin(), "R.string." + self.resourcesString[index])

    def loadLayouts(self):
        self.resourcesLayout = []
        path = self.view.window().folders()[0] + "/res/layout/"
        for path, dirs, files in os.walk(os.path.abspath(path)):
            for filename in fnmatch.filter(files, '*.xml'):
                self.resourcesLayout.append(filename.replace('.xml', ''))
        self.resourcesLayout.sort()

    def loadDrawables(self):
        self.resourcesDrawable = []
        folders = [
                    self.view.window().folders()[0] + "/res/drawable/",
                    self.view.window().folders()[0] + "/res/drawable-hdpi/",
                    self.view.window().folders()[0] + "/res/drawable-ldpi/",
                    self.view.window().folders()[0] + "/res/drawable-mdpi/"
                ]
        for folder in folders:
            for path, dirs, files in os.walk(os.path.abspath(folder)):
                for filename in fnmatch.filter(files, '*.9.png'):
                    filename = filename.replace('.9.png', '')
                    if filename not in self.resourcesDrawable:
                        self.resourcesDrawable.append(filename)
                for filename in fnmatch.filter(files, '*.png'):
                    filename = filename.replace('.png', '')
                    if filename not in self.resourcesDrawable:
                        self.resourcesDrawable.append(filename)
                for filename in fnmatch.filter(files, '*.xml'):
                    filename = filename.replace('.xml', '')
                    if filename not in self.resourcesDrawable:
                        self.resourcesDrawable.append(filename)
        self.resourcesDrawable.sort()

    def loadIds(self):
        self.resourcesId = []
        folder = self.view.window().folders()[0] + "/res/layout/"
        for path, dirs, files in os.walk(os.path.abspath(folder)):
            for filename in fnmatch.filter(files, '*.xml'):
                file = open(folder + filename, 'r')
                lines = file.readlines()
                for line in lines:
                    match = re.search("[\"|\']@\ + id\/([a-zA-Z] + [a-z_A-Z0-9]*){1}", line)
                    if match:
                        parsedId = match.group(1)
                        if parsedId not in self.resourcesId:
                            self.resourcesId.append(parsedId)
        self.resourcesId.sort(key=str.lower)

    def loadStrings(self):
        self.resourcesString = []
        folder = self.view.window().folders()[0] + "/res/"
        for path, dirs, files in os.walk(os.path.abspath(folder)):
            for filename in fnmatch.filter(files, 'strings.xml'):
                file = open(path + "/strings.xml", 'r')
                lines = file.readlines()
                for line in lines:
                    match = re.search("name\=[\"|\']([a-zA-Z] + [a-z_A-Z0-9]*)[\"|\']", line)
                    if match:
                        parsedString = match.group(1)
                        if parsedString not in self.resourcesString:
                            self.resourcesString.append(parsedString)
        self.resourcesString.sort(key=str.lower)


class CompileAndInstallToDeviceCommand(PathDependantCommands):

    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml
                p = subprocess.Popen("ant debug", cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p.stdout is not None:
                    msg = p.stdout.readlines()
                    for line in msg:
                        print line

                buildxml = path + '/build.xml'
                manifest = path + '/AndroidManifest.xml'

                projectName = self.findProject(buildxml)
                package = self.findPackage(manifest)

                settings = sublime.load_settings('Andrew.sublime-settings')
                cmd_a = settings.get('android_sdk_path') + "/platform-tools/adb -d install -r " + projectName + "-debug.apk"
                p2 = subprocess.Popen(cmd_a, cwd=path + "/bin", stdout=subprocess.PIPE, stderr=None, shell=True)
                if p2.stdout is not None:
                    msg = p2.stdout.readlines()
                    for line in msg:
                        print line
                cmd_b = settings.get('android_sdk_path') + "/platform-tools/adb shell monkey -v -p " + package + " 1"
                p3 = subprocess.Popen(cmd_b, cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p3.stdout is not None:
                    msg = p2.stdout.readlines()
                    for line in msg:
                        print line

    def findProject(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("<project ?.* name=\"([\.\ a-zA-Z1-9] + )\"", line)
            if match:
                return match.group(1)

    def findPackage(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("package=\"([\.a-zA-Z1-9] + )\"", line)
            if match:
                return match.group(1)


class InstallToDeviceCommand(PathDependantCommands):
    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml

                buildxml = path + '/build.xml'
                manifest = path + '/AndroidManifest.xml'

                projectName = self.findProject(buildxml)
                package = self.findPackage(manifest)

                settings = sublime.load_settings('Andrew.sublime-settings')
                cmd_a = settings.get('android_sdk_path') + "/platform-tools/adb -d install -r " + projectName + "-debug.apk"
                p2 = subprocess.Popen(cmd_a, cwd=path + "/bin", stdout=subprocess.PIPE, stderr=None, shell=True)
                if p2.stdout is not None:
                    msg = p2.stdout.readlines()
                    for line in msg:
                        print line
                cmd_b = settings.get('android_sdk_path') + "/platform-tools/adb shell monkey -v -p " + package + " 1"
                p3 = subprocess.Popen(cmd_b, cwd=path, stdout=subprocess.PIPE, stderr=None, shell=True)
                if p3.stdout is not None:
                    msg = p2.stdout.readlines()
                    for line in msg:
                        print line

    def findProject(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("<project ?.* name=\"([\.\ a-zA-Z1-9] + )\"", line)
            if match:
                return match.group(1)

    def findPackage(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("package=\"([\.a-zA-Z1-9] + )\"", line)
            if match:
                return match.group(1)


class BuildonSave(sublime_plugin.EventListener):

    def on_post_save(self, view):
        folder = sublime.active_window().folders()[0]
        os.chdir(folder)

        #let's see if project wants to be autobuilt.
        should_build = sublime.active_window().active_view().settings().get('build_on_save')
        if should_build == 1:
            thread = AsyncCompileDebug()
            thread.start()
            self.on_after_compile(thread)

    def on_after_compile(self, thread, i=0, dir=1):
        if thread.is_alive():
            before = i % 8
            after = (7) - before
            if not after:
                dir = -1
            if not before:
                dir = 1
            i += dir
            sublime.active_window().active_view().set_status('andrew', 'Compiling project [%s#%s]' % \
                    (' ' * before, ' ' * after))
            sublime.set_timeout(lambda: self.on_after_compile(thread, i, dir), 25)
            return
        else:
            sublime.active_window().active_view().set_status('andrew', 'Project compiled correctly')


class AsyncCompileDebug(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sublime.active_window().run_command("compile_debug")


class AsyncCompileRelease(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sublime.active_window().run_command("compile_release")


class AsyncInstallToDeviceRelease(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sublime.active_window().run_command("install_to_device")
