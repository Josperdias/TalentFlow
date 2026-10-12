; Instalador do TalentFlow People (Windows 10 1809+ / Windows 11, x64). Compilar com:
;   iscc /DAppVersion=1.3.0-rc.1 /DPublishDir=C:\caminho\publish TalentFlow.iss
#define AppName "TalentFlow People"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef PublishDir
  #define PublishDir "..\..\..\dist\windows-publish"
#endif

[Setup]
AppId={{B7C9C0E2-4F51-4C0E-9D6B-5A1F7E2D3A10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=TalentFlow
DefaultDirName={autopf}\TalentFlow People
DefaultGroupName=TalentFlow People
OutputDir=..\..\..\dist
OutputBaseFilename=TalentFlow-Setup-v{#AppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
; Instala só para o usuário atual por padrão (sem administrador); a pessoa pode escolher "para todos".
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
SetupIconFile=..\TalentFlow.Windows\Assets\talentflow.ico
UninstallDisplayIcon={app}\TalentFlow.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "{#PublishDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\TalentFlow People"; Filename: "{app}\TalentFlow.exe"
Name: "{autodesktop}\TalentFlow People"; Filename: "{app}\TalentFlow.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TalentFlow.exe"; Description: "Abrir o TalentFlow People"; Flags: nowait postinstall skipifsilent
