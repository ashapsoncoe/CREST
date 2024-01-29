# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('neuroglancer')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2] 

datas.append(('C:\\Windows\\SysWOW64\\vcruntime140.dll', '.'))


block_cipher = None


a = Analysis(['C:\\Users\\alexs\\Documents\\h01_work\\SCRIPTS\\crest_scripts\\CREST_v1.0.py'],
             pathex=['C:\\Users\\alexs\\anaconda3\\envs\\env1_from_old_laptop\\Lib\\site-packages'],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

print('hello', a.datas)

for b in a.binaries:

    if '_neuroglancer.cp39-win_amd64.pyd' in b[1]:
        print(f"Removing {b[1]}")
        a.binaries.remove(b)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
splash = Splash('C:\\Users\\alexs\\Documents\\h01_work\\CREST\\CREST_title.png',
                binaries=a.binaries,
                datas=a.datas,
                text_pos=None,
                text_size=12,
                minify_script=True)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas, 
          splash, 
          splash.binaries,
          [],
          name='CREST_v0.24',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
