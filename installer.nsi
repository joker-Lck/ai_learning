; AI 学习智能体 - NSIS 安装脚本
; 需要 NSIS 3.0+ 编译
Unicode true

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ── 基本信息 ──
Name "AI 学习智能体"
OutFile "AI学习智能体_Setup.exe"
InstallDir "$PROGRAMFILES\AI学习智能体"
InstallDirRegKey HKLM "Software\AI学习智能体" "InstallDir"
RequestExecutionLevel admin

; ── 版本信息 ──
VIProductVersion "8.6.0.0"
VIAddVersionKey "ProductName" "AI 学习智能体"
VIAddVersionKey "FileVersion" "8.6.0"
VIAddVersionKey "FileDescription" "基于多智能体的个性化学习辅助系统"
VIAddVersionKey "LegalCopyright" ""

; ── 界面配置 ──
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ── 安装页面 ──
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ── 卸载页面 ──
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── 语言 ──
!insertmacro MUI_LANGUAGE "SimpChinese"

; ── 安装区段 ──
Section "核心文件（必需）" SecCore
    SectionIn RO

    SetOutPath "$INSTDIR"

    ; PyInstaller 输出
    File /r "dist\AI学习智能体\*.*"

    ; 创建必要目录
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\exports"
    ; 创建 .env 文件（从 example 复制）
    IfFileExists "$INSTDIR\.env" env_exists
    IfFileExists "$INSTDIR\.env.example" 0 env_done
    CopyFiles "$INSTDIR\.env.example" "$INSTDIR\.env"
    Goto env_done
    env_exists:
    env_done:

    ; 写入注册表
    WriteRegStr HKLM "Software\AI学习智能体" "InstallDir" "$INSTDIR"

    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; 写入添加/删除程序
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI学习智能体" \
        "DisplayName" "AI 学习智能体"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI学习智能体" \
        "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI学习智能体" \
        "DisplayVersion" "8.6.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI学习智能体" \
        "Publisher" "AI Learning Team"
SectionEnd

Section "桌面快捷方式" SecDesktop
    CreateShortcut "$DESKTOP\AI 学习智能体.lnk" "$INSTDIR\AI学习智能体.exe" "" "$INSTDIR\AI学习智能体.exe" 0
SectionEnd

Section "开始菜单" SecStartMenu
    CreateDirectory "$SMPROGRAMS\AI 学习智能体"
    CreateShortcut "$SMPROGRAMS\AI 学习智能体\AI 学习智能体.lnk" "$INSTDIR\AI学习智能体.exe"
    CreateShortcut "$SMPROGRAMS\AI 学习智能体\卸载.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

; ── 区段描述 ──
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "核心程序文件，包括后端、前端、数据库等组件。"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "在桌面创建快捷方式。"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "在开始菜单创建程序组。"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ── 安装后操作 ──
Function .onInstSuccess
    MessageBox MB_YESNO "安装完成！是否立即启动 AI 学习智能体？" IDNO NoLaunch
    Exec "$INSTDIR\AI学习智能体.exe"
    NoLaunch:
FunctionEnd

; ── 卸载区段 ──
Section "Uninstall"
    ; 停止可能运行的进程
    nsExec::ExecToLog 'taskkill /F /IM "AI学习智能体.exe" /T'
    nsExec::ExecToLog 'taskkill /F /IM "node.exe" /T'

    Sleep 2000

    ; 删除文件
    RMDir /r "$INSTDIR\_internal"
    RMDir /r "$INSTDIR\frontend"
    RMDir /r "$INSTDIR\node"
    RMDir /r "$INSTDIR\data"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\scripts"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\exports"
    Delete "$INSTDIR\AI学习智能体.exe"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\.env"
    Delete "$INSTDIR\.env.example"
    RMDir "$INSTDIR"

    ; 删除快捷方式
    Delete "$DESKTOP\AI 学习智能体.lnk"
    RMDir /r "$SMPROGRAMS\AI 学习智能体"

    ; 删除注册表
    DeleteRegKey HKLM "Software\AI学习智能体"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI学习智能体"
SectionEnd
