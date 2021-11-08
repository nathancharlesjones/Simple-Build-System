from helper import (execute_shell_cmd, find, get_dependencies_list,
                    file_does_not_exist, at_least_one_dependency_is_newer_than,
                    get_file_extension, list_of_files_contains_c_files,
                    list_of_files_contains_cpp_files, list_of_files_contains_s_or_S_files)
import os

# TODO: Add more comments

class target:
    """ Parent class for defining project targets. """

    def __init__(self):
        raise NameError("Class target does not support creating objects; use target.executable or target.library instead.")
    
    def build(self, verbose=False):
        for pre_build_cmd in self.pre_build_cmds:
            execute_shell_cmd(pre_build_cmd, verbose)
        
        self.compile_object_files(verbose)
        self.build_local_dependencies(verbose)
        
        if self.target_needs_building():
            build_cmd = self.form_build_cmd()
            execute_shell_cmd(build_cmd, verbose)
        else:
            print("Nothing to be done for {0}".format(self.name))
        
        for post_build_cmd in self.post_build_cmds:
            execute_shell_cmd(post_build_cmd, verbose)

    def build_local_dependencies(self, verbose=False):
        for this_target in self.local_dependencies:
            this_target.build()

    def clean(self, verbose=False):
        execute_shell_cmd("find {0}".format(self.build_dir)+r" -mindepth 1 -maxdepth 1 -type d -exec rm -r {} \;", verbose)
    
    def compile_object_files(self, verbose=False):
        for this_source_file in self.source_files:
            self.make_build_dir_for_obj_file(this_source_file)

            if get_file_extension(this_source_file) == ".cpp":
                program = self.cpp_compiler
                flags = self.cpp_flags
            elif get_file_extension(this_source_file) == ".c":
                program = self.c_compiler
                flags = self.c_flags
            elif get_file_extension(this_source_file) == ".s" or get_file_extension(this_source_file) == ".S":
                program = self.assembler
                flags = self.as_flags
            else:
                raise ValueError("Unrecognized file extension in source files: {0}".format(get_file_extension(this_source_file)))

            obj_file_and_path = self.get_obj_file_and_path_from_source_file(this_source_file)
                
            if self.object_file_needs_building(obj_file_and_path):
                flags_str = ' '.join(flags)
                defines_str = ' '.join(["-D"+define for define in self.defines])
                include_dirs_str = ' '.join(["-I "+inc_dir for inc_dir in self.include_dirs])
                dep_file_and_path = self.get_dep_file_and_path_from_obj_file_and_path(obj_file_and_path)
                compile_obj_file_cmd = " ".join([program,flags_str,defines_str,include_dirs_str,"-MMD -MF",dep_file_and_path,"-c",this_source_file,"-o",obj_file_and_path])
                execute_shell_cmd(compile_obj_file_cmd, verbose)
            else:
                print("Nothing to be done for {0}".format(obj_file_and_path))

    def execute(self, cmd, verbose=False):
        if cmd == 'clean':
            self.clean(verbose)
        elif cmd == 'purify':
            self.purify(verbose)
        elif cmd == 'zip':
            self.zip(verbose)
        elif cmd == 'list':
            self.show(verbose)
        elif cmd == 'build':
            self.build(verbose)

    def form_build_cmd(self, verbose=False):
        pass
    
    def get_dep_file_and_path_from_obj_file_and_path(self, obj_file_and_path, verbose=False):
        return obj_file_and_path.replace(".o",".d")

    def get_obj_file_and_path_from_source_file(self, source_file, verbose=False):
        obj_file = source_file.replace(get_file_extension(source_file),".o")
        return "{0}/{1}".format(self.build_dir,obj_file)

    def make_build_dir_for_obj_file(self, source_file, verbose=False):
        path, filename = os.path.split(source_file)
        execute_shell_cmd("mkdir -p {0}/{1}".format(self.build_dir, path), verbose)

    def object_file_needs_building(self, obj_file_and_path, verbose=False):
        dep_file_and_path = self.get_dep_file_and_path_from_obj_file_and_path(obj_file_and_path)
        dep_list = get_dependencies_list(dep_file_and_path)
        return file_does_not_exist(obj_file_and_path) or file_does_not_exist(dep_file_and_path) or at_least_one_dependency_is_newer_than(obj_file_and_path, dep_list)

    def purify(self, verbose=False):
        execute_shell_cmd("rm -r -f {0}".format(self.build_dir), verbose)

    def show(self, verbose=False):
        pass

    def target_needs_building(self, verbose=False):
        return file_does_not_exist(self.target_file_and_path) or at_least_one_dependency_is_newer_than(self.target_file_and_path, self.object_files+self.local_dep_target_list)

    def zip(self, verbose=False):
        execute_shell_cmd("zip -r {0}/{1}.zip {2} {3}".format(self.build_dir,self.name,self.target_file_and_path,self.local_dep_target_list), verbose)

    def __str__(self):
        pass

class executable(target):
    """ Helpful docstring """

    def __init__(self,linker,build_dir,target,source_files,name='unnamed target',
        assembler='',as_flags=[],c_compiler='',c_flags=[],cpp_compiler='',cpp_flags=[],
        defines=[],linker_flags=[],include_dirs=[],libraries=[],library_dirs=[],
        linker_script='',local_dependencies=[],pre_build_cmds=[],post_build_cmds=[]):
        """ Helpful docstring """
        self.name = name

        self.source_files = source_files

        if len(self.source_files) == 0:
            raise ValueError("No source files listed for {0}".format(self.name))
        
        self.cpp_compiler = cpp_compiler
        self.cpp_flags = cpp_flags
        if list_of_files_contains_cpp_files(self.source_files) and self.cpp_compiler == '':
            raise ValueError("C++ compiler not specified though .cpp files are listed amongst the source files.")

        self.c_compiler = c_compiler        
        self.c_flags = c_flags
        if list_of_files_contains_c_files(self.source_files) and self.c_compiler == '':
            raise ValueError("C compiler not specified though .c files are listed amongst the source files; use the same program as the C++ compiler if that is intended to compile both.")
        
        self.assembler = assembler
        self.as_flags = as_flags
        if list_of_files_contains_s_or_S_files(self.source_files) and self.assembler == '':
            raise ValueError("Assembler not specified though .s/.S files are listed in the source files; use the same program as the C/C++ compiler if that is intended to compile/assemble both.")
        
        self.defines = defines
        
        self.linker = linker
        self.linker_flags = linker_flags
        self.linker_script = linker_script
        
        self.build_dir = build_dir
        
        self.target = target

        self.target_file_and_path = "{0}/{1}".format(self.build_dir, self.target)
        
        self.include_dirs = include_dirs
        
        self.object_files = []
        for this_source_file in self.source_files:
            self.object_files.append("{0}/{1}".format(self.build_dir,this_source_file.replace(get_file_extension(this_source_file), ".o")))
        
        self.libraries = libraries
        
        self.library_dirs = library_dirs
        
        self.local_dependencies = local_dependencies
        self.local_dep_target_list = ["{0}/{1}".format(dep.build_dir,dep.target) for dep in self.local_dependencies]
        
        self.pre_build_cmds = pre_build_cmds
        
        self.post_build_cmds = post_build_cmds

    def form_build_cmd(self, verbose=False):
        linker_flags_str = ' '.join(self.linker_flags)
        defines_str = ' '.join(["-D"+define for define in self.defines])
        include_dirs_str = ' '.join(["-I "+inc_dir for inc_dir in self.include_dirs])
        object_files_str = ' '.join(self.object_files)
        library_dirs_str = ' '.join(["-L "+lib_dir for lib_dir in self.library_dirs])
        libraries_str = ' '.join(["-l"+lib for lib in self.libraries])
        linker_script_with_flag_if_present = '-T {0}'.format(self.linker_script) if self.linker_script != '' else ''
        return " ".join([self.linker,linker_flags_str,linker_script_with_flag_if_present,defines_str,include_dirs_str,object_files_str,library_dirs_str,libraries_str,"-o",self.target_file_and_path])

    def show(self, verbose=False):
        if not verbose:
            print("- {0}".format(self.name))
        else:
            print(self)

    def __str__(self):
        repr = '''{1} is defined as follows:
- {0}{1}
- {2}{3}
- {4}{5}
- {6}{7}
- {8}{9}
- {10}{11}
- {12}{13}
- {14}{15}
- {16}{17}
- {18}{19}
- {20}{21}
- {22}{23}
- {24}{25}
- {26}{27}
- {28}{29}
- {30}{31}
- {32}{33}
- {34}{35}
- {36}{37}
- {38}{39} '''.format( "name:".ljust(25,'.'),
                        self.name,
                        "target:".ljust(25,'.'),
                        self.target,
                        "build_dir:".ljust(25,'.'),
                        self.build_dir,
                        "assembler:".ljust(25,'.'),
                        self.assembler,
                        "as_flags:".ljust(25,'.'),
                        self.as_flags,
                        "c_compiler:".ljust(25,'.'),
                        self.c_compiler,
                        "c_flags:".ljust(25,'.'),
                        self.c_flags,
                        "cpp_compiler:".ljust(25,'.'),
                        self.cpp_compiler,
                        "cpp_flags:".ljust(25,'.'),
                        self.cpp_flags,
                        "linker:".ljust(25,'.'),
                        self.linker,
                        "linker_flags:".ljust(25,'.'),
                        self.linker_flags,
                        "linker_script:".ljust(25,'.'),
                        self.linker_script,
                        "defines:".ljust(25,'.'),
                        self.defines,
                        "include_dirs:".ljust(25,'.'),
                        self.include_dirs,
                        "source_files:".ljust(25,'.'),
                        self.source_files,
                        "libraries:".ljust(25,'.'),
                        self.libraries,
                        "library_dirs:".ljust(25,'.'),
                        self.library_dirs,
                        "local_dependencies:".ljust(25,'.'),
                        [dep.name for dep in self.local_dependencies],
                        "pre_build_cmds:".ljust(25,'.'),
                        self.pre_build_cmds,
                        "post_build_cmds:".ljust(25,'.'),
                        self.post_build_cmds)
        return repr

class library(target):
    """ Helpful docstring """

    def __init__(self,archiver,build_dir,target,source_files,name='unnamed target',
        assembler='',as_flags=[],c_compiler='',c_flags=[],cpp_compiler='',cpp_flags=[],
        defines=[],archiver_flags=[],include_dirs=[],libraries=[],
        library_dirs=[],local_dependencies=[],pre_build_cmds=[],post_build_cmds=[]):
        """ Helpful docstring """
        self.name = name

        self.source_files = source_files
        if len(self.source_files) == 0:
            raise ValueError("No source files listed for {0}".format(self.name))
        
        self.cpp_compiler = cpp_compiler
        self.cpp_flags = cpp_flags
        if list_of_files_contains_cpp_files(self.source_files) and self.cpp_compiler == '':
            raise ValueError("C++ compiler not specified though .cpp files are listed amongst the source files.")

        self.c_compiler = c_compiler        
        self.c_flags = c_flags
        if list_of_files_contains_c_files(self.source_files) and self.c_compiler == '':
            raise ValueError("C compiler not specified though .c files are listed amongst the source files; use the same program as the C++ compiler if that is intended to compile both.")
        
        self.assembler = assembler
        self.as_flags = as_flags
        if list_of_files_contains_s_or_S_files(self.source_files) and self.assembler == '':
            raise ValueError("Assembler not specified though .s/.S files are listed in the source files; use the same program as the C/C++ compiler if that is intended to compile/assemble both.")
        
        self.defines = defines
        
        self.archiver = archiver
        
        self.archiver_flags = archiver_flags
        
        self.build_dir = build_dir
        
        self.target = target

        self.target_file_and_path = "{0}/{1}".format(self.build_dir, self.target)
        
        self.include_dirs = include_dirs
        
        self.object_files = []
        for this_source_file in self.source_files:
            self.object_files.append("{0}/{1}".format(self.build_dir,this_source_file.replace(get_file_extension(this_source_file), ".o")))
        
        self.libraries = libraries
        
        self.library_dirs = library_dirs
        
        self.local_dependencies = local_dependencies
        self.local_dep_target_list = ["{0}/{1}".format(dep.build_dir,dep.target) for dep in self.local_dependencies]
        
        self.pre_build_cmds = pre_build_cmds
        
        self.post_build_cmds = post_build_cmds

    def form_build_cmd(self, verbose=False):
        archiver_flags_str = ' '.join(self.archiver_flags)
        defines_str = ' '.join(["-D"+define for define in self.defines])
        object_files_str = ' '.join(self.object_files)
        return " ".join([self.archiver,archiver_flags_str,defines_str,self.target_file_and_path,object_files_str])

    def show(self, verbose=False):
        if not verbose:
            print("- {0}".format(self.name))
        else:
            print(self)

    def __str__(self):
        repr = '''{1} is defined as follows:
- {0}{1}
- {2}{3}
- {4}{5}
- {6}{7}
- {8}{9}
- {10}{11}
- {12}{13}
- {14}{15}
- {16}{17}
- {18}{19}
- {20}{21}
- {22}{23}
- {24}{25}
- {26}{27}
- {28}{29}
- {30}{31}
- {32}{33}
- {34}{35}
- {36}{37} '''.format( "name:".ljust(25,'.'),
                        self.name,
                        "target:".ljust(25,'.'),
                        self.target,
                        "build_dir:".ljust(25,'.'),
                        self.build_dir,
                        "assembler:".ljust(25,'.'),
                        self.assembler,
                        "as_flags:".ljust(25,'.'),
                        self.as_flags,
                        "c_compiler:".ljust(25,'.'),
                        self.c_compiler,
                        "c_flags:".ljust(25,'.'),
                        self.c_flags,
                        "cpp_compiler:".ljust(25,'.'),
                        self.cpp_compiler,
                        "cpp_flags:".ljust(25,'.'),
                        self.cpp_flags,
                        "archiver:".ljust(25,'.'),
                        self.archiver,
                        "archiver_flags:".ljust(25,'.'),
                        self.archiver_flags,
                        "defines:".ljust(25,'.'),
                        self.defines,
                        "include_dirs:".ljust(25,'.'),
                        self.include_dirs,
                        "source_files:".ljust(25,'.'),
                        self.source_files,
                        "libraries:".ljust(25,'.'),
                        self.libraries,
                        "library_dirs:".ljust(25,'.'),
                        self.library_dirs,
                        "local_dependencies:".ljust(25,'.'),
                        [dep.name for dep in self.local_dependencies],
                        "pre_build_cmds:".ljust(25,'.'),
                        self.pre_build_cmds,
                        "post_build_cmds:".ljust(25,'.'),
                        self.post_build_cmds)
        return repr
