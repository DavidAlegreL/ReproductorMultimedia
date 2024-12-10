[Setup]
AppName=MiReproductorMultimedia
AppVersion=1.0
DefaultDirName={pf}\MiReproductorMultimedia
DefaultGroupName=MiReproductorMultimedia
OutputBaseFilename=MiReproductorMultimediaInstaller
Compression=lzma
SolidCompression=yes

[Files]
; Ajusta la ruta del ejecutable y/o assets según corresponda
Source="C:\Users\David\Desktop\uni\cuarto\Multimedia\Multimedia\dist\main.exe"; DestDir="{app}"

; Carpeta de assets
Source="C:\Users\David\Desktop\uni\cuarto\Multimedia\Multimedia\assets\*"; DestDir="{app}\assets"; Flags: recursesubdirs createallsubdirs

; Instaldor de MediaInfo, se copia al directorio temporal {tmp}
Source="C:\Users\David\Desktop\uni\cuarto\Multimedia\Multimedia\MediaInfo_Installer.exe"; DestDir="{tmp}"

[Icons]
Name="{group}\Mi Reproductor Multimedia"; Filename="{app}\main.exe"
Name="{group}\Desinstalar Mi Reproductor Multimedia"; Filename="{uninstallexe}"

[Run]
; Primero instalamos MediaInfo en modo silencioso
Filename="{tmp}\MediaInfo_Installer.exe"; Parameters="/S"

; Luego ejecutamos la aplicación
Filename="{app}\main.exe"; Description="Ejecutar Mi Reproductor Multimedia"


