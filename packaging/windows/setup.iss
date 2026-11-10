#define ProductName "Ma Médiathèque"
#define Publisher "Trucabule"
#define Executable "Ma-Mediatheque.exe"
#define ShellId "Trucabule.MaMediatheque"

[Setup]
AppId={{B1ED9389-11A8-4B40-A67B-C427701D3B2B}
AppName={#ProductName}
AppVersion={#ProductVersion}
AppPublisher={#Publisher}
AppPublisherURL=https://www.trucabule.fr/
VersionInfoVersion={#WindowsVersion}
VersionInfoProductVersion={#WindowsVersion}
VersionInfoTextVersion={#ProductVersion}
VersionInfoProductTextVersion={#ProductVersion}
VersionInfoProductName={#ProductName}
VersionInfoCompany={#Publisher}
DefaultDirName={localappdata}\Programs\Ma Mediatheque
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
UseSetupLdr=x64
SetupArchitecture=x64
MinVersion=10.0.22000
SetupIconFile={#SourceDir}\_internal\catalogue\art\Ma-Mediatheque.ico
UninstallDisplayName={#ProductName}
UninstallDisplayIcon={app}\{#Executable}
CloseApplications=yes
RestartApplications=no
Compression=lzma2
SolidCompression=yes
OutputDir={#OutputDir}
OutputBaseFilename=Ma-Mediatheque-{#ProductVersion}-windows-x64-setup
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#ProductName}"; Filename: "{app}\{#Executable}"; WorkingDir: "{app}"; AppUserModelID: "{#ShellId}"
Name: "{userdesktop}\{#ProductName}"; Filename: "{app}\{#Executable}"; WorkingDir: "{app}"; AppUserModelID: "{#ShellId}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#Executable}"; Description: "{cm:LaunchProgram,{#ProductName}}"; Flags: nowait postinstall skipifsilent
