[Setup]
AppName=TrackingSystem
AppVersion=1.0
DefaultDirName={pf}\TrackingSystem
DefaultGroupName=TrackingSystem
OutputDir=Output
OutputBaseFilename=TrackingSystemSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
; Main executable (OneFile Mode)
Source: "dist\TrackingSystem.exe"; DestDir: "{app}"; Flags: ignoreversion

; Configuration (External)
Source: ".env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

; Database support (Docker Compose)
Source: "docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data\faces"
Name: "{app}\data\zonas"
Name: "{app}\data\snapshots"

[Icons]
Name: "{group}\TrackingSystem"; Filename: "{app}\TrackingSystem.exe"
Name: "{commondesktop}\TrackingSystem"; Filename: "{app}\TrackingSystem.exe"

[Code]
function InitializeSetup(): Boolean;
var
  DockerInstalled: Boolean;
begin
  Result := True;

  if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Docker Inc.\Docker\1.0') then
  begin
    DockerInstalled := True;
  end
  else
  begin
    DockerInstalled := False;
    if MsgBox('Docker Desktop is required for the Database but was not detected.' #13#10 'Do you want to continue anyway? (You will need to install Docker manually)', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

[Run]
Filename: "{app}\TrackingSystem.exe"; Description: "Launch TrackingSystem"; Flags: nowait postinstall skipifsilent
