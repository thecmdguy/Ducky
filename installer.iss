; -------------------------------------------------------------
;  Ducky Network & Security Tool — Inno Setup 6 Script
;  Output: installer\Ducky-Setup-{version}.exe
;
;  Compile with:  build_installer.ps1
;  Or manually:   ISCC.exe installer.iss
; -------------------------------------------------------------

#define MyAppName      "Ducky"
#define MyAppVersion   "1.3.0"
#define MyAppPublisher "thecmdguy"
#define MyAppURL       "https://github.com/thecmdguy/Ducky"
#define MyAppExeName   "Ducky.exe"
#define MyBuildDir     "dist\Ducky"
#define MyIconFile     "src\ducky_app\assets\ducky_icon.ico"

[Setup]
; AppId GUID — must never change between versions (used for upgrades and uninstall)
AppId={{D7A2E8F3-4B1C-4E9A-8F2D-5C3B7E1A9F4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Default install to Program Files or user's AppData depending on privileges
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Show license during install
LicenseFile=LICENSE

; Output
OutputDir=installer
OutputBaseFilename=Ducky-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes

; Icons
SetupIconFile={#MyIconFile}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; Modern wizard (Inno Setup 6+)
WizardStyle=modern
WizardSmallImageFile={#MyIconFile}

; Let user choose between per-user and machine-wide install
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Version info embedded in setup exe
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; Automatically handle previous version upgrades
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
  Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copy entire PyInstaller build output into the install directory
Source: "{#MyBuildDir}\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; \
  Filename: "{app}\{#MyAppExeName}"; \
  Comment: "Open Ducky Network & Security Tool"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; \
  Filename: "{uninstallexe}"

; Desktop (optional — controlled by task above)
Name: "{autodesktop}\{#MyAppName}"; \
  Filename: "{app}\{#MyAppExeName}"; \
  Tasks: desktopicon

[Run]
; Offer to launch the app when the installer finishes
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[Code]
// ---------------------------------------------------------------------------
// Check for Npcap at install time and warn the user if it is missing.
// Npcap (https://npcap.com) is required for the Topology Mapper and
// Connected Devices features. The rest of the app works without it.
// ---------------------------------------------------------------------------

function NpcapInstalled(): Boolean;
var
  DllPath: String;
begin
  DllPath := ExpandConstant('{sys}\Npcap\wpcap.dll');
  Result := FileExists(DllPath);
  if not Result then
  begin
    DllPath := ExpandConstant('{sys}\wpcap.dll');
    Result := FileExists(DllPath);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not NpcapInstalled() then
    begin
      MsgBox(
        'Ducky was installed successfully!' + #13#10 + #13#10 +
        'Optional: Network scanning features (Topology Mapper and Connected' + #13#10 +
        'Devices) require Npcap to be installed.' + #13#10 + #13#10 +
        'Download Npcap for free from: https://npcap.com' + #13#10 + #13#10 +
        'All other features work without it.',
        mbInformation,
        MB_OK
      );
    end;
  end;
end;
