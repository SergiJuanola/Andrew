"""
Andrew Plugin for Sublime Text 2
@author Sergi Juanola
@version 0.3
"""
# -*- coding: utf-8 -*-
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
                m1 = re.search(r'[\ ]*Name: ([a-zA-Z0-9\ \.]*)', row1)
                m2 = re.search(r'(android-[0-9]+)', row2)
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

    resources_dict = {}
    options = []
    options_index = -1
    edit = 0

    def run(self, edit):
        self.resources_dict = sublime.active_window().active_view().settings().get('R', {})

        if len(self.resources_dict.keys()) == 0:
            sublime.active_window().run_command("parse_resources")
            self.resources_dict = sublime.active_window().active_view().settings().get('R', {})

        self.options = self.resources_dict.keys()
        self.options.sort()
        self.edit = edit
        self.view.window().show_quick_panel(self.options, self.on_done)

    def on_done(self, index):
        if index is not -1:
            self.options_index = index
            self.view.window().show_quick_panel(self.resources_dict[self.options[index]], self.on_done_choose)

    def on_done_choose(self, index):
        if index is not -1:
            self.view.insert(self.edit, self.view.sel()[0].begin(), "R." + self.options[self.options_index] + "." + self.resources_dict[self.options[self.options_index]][index])


class CompileAndInstallToDeviceCommand(PathDependantCommands):

    def run(self):
        thread = AsyncInstallToDevice()
        thread.start()
        self.handle_thread(thread)

    def findProject(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search(r"<project ?.* name=\"([\.\ a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def findPackage(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search(r"package=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def handle_thread(self, thread, i=0, dir=1):
        if thread.is_alive():
            before = i % 8
            after = (7) - before
            if not after:
                dir = -1
            if not before:
                dir = 1
            i += dir

            if thread.phase == 1:
                state_name = 'Compiling project'
            elif thread.phase == 2:
                state_name = 'Installing to device'
            sublime.active_window().active_view().set_status('andrew', state_name + ' [%s#%s]' % (' ' * before, ' ' * after))
            sublime.set_timeout(lambda: self.handle_thread(thread, i, dir), 25)
            return
        else:
            sublime.active_window().active_view().set_status('andrew', 'Project installed correctly')


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
            match = re.search(r"<project ?.* name=\"([\.\ a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def findPackage(self, xmlFile):
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search(r"package=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)


class BuildonSave(sublime_plugin.EventListener):

    def on_post_save(self, view):
        #let's see if project wants to be autobuilt.
        should_build = sublime.load_settings('Andrew.sublime-settings').get('compile_on_save')
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


class CompileOnSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        compile_on_save = settings.get('compile_on_save')
        if compile_on_save == 1:
            settings.set('compile_on_save', 0)
        else:
            settings.set('compile_on_save', 1)
        sublime.save_settings('Andrew.sublime-settings')

    def is_checked(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        compile_on_save = settings.get('compile_on_save', 0)
        if compile_on_save == 1:
            return True
        else:
            return False


class AsyncCompileDebug(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sublime.active_window().run_command("compile_debug")
        sublime.active_window().run_command("parse_resources")


class AsyncCompileRelease(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sublime.active_window().run_command("compile_release")


class AsyncInstallToDevice(threading.Thread):

    phase = 0

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        settings = sublime.load_settings('Andrew.sublime-settings')
        compile_on_save = settings.get('compile_on_save', 0)
        if compile_on_save == 0:
            self.phase = 1
            sublime.active_window().run_command("compile_debug")
        self.phase = 2
        sublime.active_window().run_command("install_to_device")


class ParseResourcesCommand(PathDependantCommands):

    def run(self):
        resources_dict = {}
        for folder in self.window.folders():
            resources = self.locatePath("R.java", folder)
            if resources is not None:
                file = open(resources + "/R.java", 'r')
                resources_text = file.read()
                resource_types = re.findall(r'public static final class ([a-z]+) {([a-z=0-9;\t _\n]*)}', resources_text)
                for resource_type in resource_types:
                    resource_name = resource_type[0]
                    resource_ids = []
                    resource_vars = re.findall(r'public static final int ([a-zA-Z0-9_]+)=', resource_type[1])
                    for resource_var in resource_vars:
                        resource_ids.append(resource_var)
                    if len(resource_ids):
                        resources_dict[resource_name] = resource_ids
                settings = sublime.active_window().active_view().settings()
                settings.set('R', resources_dict)


class RefactorStringCommand(sublime_plugin.TextCommand):

    text = ""
    tag = ""
    region = None
    edit = None

    def run(self, edit):
        self.edit = edit
        sels = self.view.sel()
        new_sels = []
        for sel in sels:
            begin = sel.a
            end = sel.b
            while self.view.substr(begin) != '"':
                begin -= 1
            begin += 1
            while self.view.substr(end) != '"':
                end += 1
            new_sels.append(sublime.Region(begin, end))
        for sel in new_sels:
            self.text = self.view.substr(sel)
            self.tag = self.slugify(self.view.substr(sel))
            self.region = sel
            sublime.active_window().show_input_panel("String name:", self.tag, self.on_done, None, None)

    def on_done(self, text):
        """if index < 0:
            return
        snippet = self.snippets[index]
        self.view.run_command('insert_snippet', {"name": "Packages/Andrew/snippets/" + snippet + ".sublime-snippet"})"""
        self.tag = text
        self.add_to_strings_xml(self.text, self.tag)

    def slugify(self, str):
        str = str.lower()
        return re.sub(r'\W+', '_', str)

    def add_to_strings_xml(self, text, tag):
        for folder in sublime.active_window().folders():
            stringsxml = self.locatePath("strings.xml", folder)
            if stringsxml is not None:
                stringsxml += "/strings.xml"
                file = open(stringsxml, 'r')
                strings_content = file.read()
                file.close()
                file = open(stringsxml, 'w')
                new_block = '<string name="' + tag + '">' + text + '</string>'
                strings_content = strings_content.replace("</resources>", "\t" + new_block + "\n</resources>")
                sublime.active_window().active_view().replace(self.edit, self.region, "@string/" + self.tag)
                print strings_content
                file.write(strings_content)
                file.close()

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path
