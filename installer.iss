; Facebook Group Scraper Installer Script
; Dibuat dengan Inno Setup Compiler

#define MyAppName "Facebook Group Scraper"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Metabiora"
#define MyAppPublisherURL "https://github.com/Odnson"
#define MyAppExeName "FacebookScraperGUI.exe"
#define MyAppAssocName "Facebook Group Scraper"
#define MyAppExtension ".fgs"

[Setup]
; Informasi dasar
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppPublisherURL}
AppSupportURL={#MyAppPublisherURL}
AppUpdatesURL={#MyAppPublisherURL}
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Izinkan user pilih lokasi install
DisableDirPage=no
DisableProgramGroupPage=no
; Output
OutputBaseFilename=FacebookGroupScraper_Setup
OutputDir=installer_output
Compression=lzma
SolidCompression=yes
; Wizard
WizardStyle=modern
; WizardImageFile=installer_wizard.bmp
; WizardSmallImageFile=installer_small.bmp
; Permissions
PrivilegesRequired=admin
; Icon
; SetupIconFile=icon.ico
; UninstallIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; GUI EXE
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; CLI EXE (jika ada)
Source: "dist\FacebookScraperCLI.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; Config file template
Source: "scraper_config.json"; DestDir: "{app}"; Flags: ignoreversion
; README
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; Dependencies
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "https://github.com"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Hapus registry saat uninstall
Root: HKCU; Subkey: "Software\FacebookGroupScraper"; ValueType: none; Flags: deletekey uninsdeletekeyifempty

[UninstallDelete]
; Hapus config file saat uninstall (opsional, comment jika ingin menyimpan)
; Type: files; Name: "{app}\scraper_config.json"
