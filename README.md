# skel
A minimalist tool that generates skeleton directories based on XML files.

## Installation
Clone this repo and place it in your home directory (or anywhere you like). `cd` into the repo and run the setup script.
```
cd /path/to/cloned/repo
./setup.sh
```
At this point, you have a few options:
- Add the `bin` directory inside the application's installation directory to `PATH`
- Add a symbolic link somewhere onto your `PATH`. The symlink should point to `/path/to/cloned/repo/bin/skel`
- Define an alias that your shell will translate to the full path of the executable. E.g: `alias skel="/path/to/cloned/repo/bin/skel"` 

## Usage
```
skel <template> [targets...]
```

`<template>` refers to the XML file that `skel` will use to generate the skeleton directory. All template files are stored in the `resources/templates` subdirectory of the application's installation directory.

`[targets...]` are the directories that `skel` will use as the root for the generated skeletons. `[targets]` can be omitted, in which case `skel` will generate the skeleton directory structure in the current working directory.
If one of the `[targets]` is a relative path, `skel` will look for the target directory in the current working directory; if the specified targets aren't found, `skel` will create them in the current working directory.

_The following explanation assumes that `skel` is installed in `~/skel`_.
### Examples:
```
skel gradle-java
```
This tells `skel` to search for an XML file called `gradle-java.xml` inside `~/skel/resources/templates` and then generate a skeleton structure inside the current working directory based on the file.   

```
skel gradle-java someproject
```
`skel` will use `~/skel/resources/templates/gradle-java.xml` to generate a skeleton structure inside a directory named `someproject` in the current working directory. 

## Specification Format
The desired directory structure can be completely specified using simple XML files. 

### Example:
```xml
<!--~/skel/resources/templates/gradle-java.xml-->
<root>
    <dir name="src">
         <dir name="main">
             <dir name="java">
                   <file name="HelloWorld.java"/>
             </dir>
         </dir>

         <dir name="test">
             <dir name="java">
                  <file name="HelloWorldTest.java"/>
             </dir>
         </dir>
    </dir>
</root>
```
Running `skel` with the above specification file ```skel gradle-java subproject``` will result in the following directory structure:
```
.
└── src
    ├── main
    │   └── java
    │       └── HelloWorld.java
    └── test
        └── java
            └── HelloWorldTest.java
```


### XML Elements
`skel` only understands XML specification files containing **ONLY** the following elements: `<root>`, `<dir>`, and `<file>`


`<root>`
- Denotes the root directory of the resulting skeleton.
- Contains all the other elements in the specification file.
- Cannot be nested inside any other elements (must be top-level).

`<dir>`
- Represents a directory to be created in the skeleton.
- Can contain any number of children, which can be `<dir>`s or `<file>`s.
- Children of a `<dir>` represents the entities that the resulting directory will contain in the generated skeleton.
- The `name` attribute is **mandatory**, which represents the basename of the corresponding directory in the skeleton.
- E.g: `<dir name="foobar"/>` represents a directory named `foobar` within its containing directory.

`<file>`
- Represents a file to be created.
- This element should not contain any children (if it does, the children will be ignored).
- The `name` attribute is also **mandatory**, which represents the basename of the created file.
- An optional `src` attribute can be specified, which is a path (absolute or relative) that points to an existing file whose contents will be copied into the generated file.
    - If a relative path is supplied to `src`, the path will be resolved relative to the `resources/filesrc` directory inside the application's installation directory.
    - E.g: `<file name="build.gradle.kts" src="sample-buildscript.kts"/>` will create a file named `build.gradle.kts` whose contents are the same as `~/skel/resources/filesrc/sample-buildscript.kts`

## Example Specification Files
```xml
<!-- gradle-java.xml -->
<root>
    <!-- Settings file -->
    <file name="settings.gradle.kts" src="gradle-settings-template">

    <!-- Subproject -->
    <dir name="app">

        <!-- Build script -->
        <file name="build.gradle.kts" src="sample-buildscript"/>

        <!-- Source directory -->
        <dir name="src">
            <dir name="main">
                <dir name="java">
                     <file name="App.java"/>
                </dir>

                <dir name="resources></dir>
            </dir>
            <dir name="test">
                <dir name="java">
                    <file name="AppTest.java"/>
                </dir>
                <dir name="resources></dir>
            </dir>
        </dir>
    </dir>
    
</root>
```
