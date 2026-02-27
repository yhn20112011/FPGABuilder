; FPGABuilder安装脚本
; 由packager.py自动生成

#define MyAppName "FPGABuilder"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "YiHok"
#define MyAppURL "https://github.com/yhn20112011/FPGABuilder"
#define MyAppExeName "FPGABuilder.exe"

[Setup]
AppId={{FC2B9F7F-3B2A-4B8E-9F6D-7C8E5A3B2D1A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={{autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile={{src}\LICENSE
OutputDir={#OutputDir}
OutputBaseFileName=FPGABuilder-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}"; GroupDescription: "{{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{{src}\dist\FPGABuilder.exe"; DestDir: "{{app}"; Flags: ignoreversion
Source: "{{src}\README.md"; DestDir: "{{app}"; Flags: ignoreversion
Source: "{{src}\LICENSE"; DestDir: "{{app}"; Flags: ignoreversion
Source: "{{src}\docs\*"; DestDir: "{{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}\{#MyAppName}"; Filename: "{{app}\{#MyAppExeName}"
Name: "{{group}\{{cm:UninstallProgram,{#MyAppName}}"; Filename: "{{uninstallexe}"
Name: "{{commondesktop}\{#MyAppName}"; Filename: "{{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{{app}\{#MyAppExeName}"; Description: "{{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // 检查Python是否安装（可选）
  // 检查依赖等
end;
