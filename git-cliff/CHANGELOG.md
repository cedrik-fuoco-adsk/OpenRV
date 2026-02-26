## [Unreleased]

### #578

- Update to FFmpeg 7.1 (#599) ([#599](https://github.com/AcademySoftwareFoundation/OpenRV/pull/599))

### #604

- Fix Blackmagic Video Output plugin build on Windows (#605) ([#605](https://github.com/AcademySoftwareFoundation/OpenRV/pull/605))

### #616

- Fix crash when prog source loading enabled (#617) ([#617](https://github.com/AcademySoftwareFoundation/OpenRV/pull/617))

### 1004

- Update window title on source media rep change - SG-41311 (#1005) ([#1005](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1005))

### 433

- Fix Playback stopping when RV is completely overlapped on macOS (#434) ([#434](https://github.com/AcademySoftwareFoundation/OpenRV/pull/434))

### 457

- Fix OCIO failure with 1D LUTs of 2048 length (#627) ([#627](https://github.com/AcademySoftwareFoundation/OpenRV/pull/627))

### 463

- Unanonymised QMutexLocker usage in OCIOIPNode.cpp (#476) ([#476](https://github.com/AcademySoftwareFoundation/OpenRV/pull/476))

### 558

- Add Debugging Switches Documentation (#782) ([#782](https://github.com/AcademySoftwareFoundation/OpenRV/pull/782))

### 600

- Fix mov container getting wrong frame rate (#662) ([#662](https://github.com/AcademySoftwareFoundation/OpenRV/pull/662))

### 616

- Fix MediaLibrary crash when prog source loading enabled (#643) ([#643](https://github.com/AcademySoftwareFoundation/OpenRV/pull/643))

### 620

- Fix overrides of video output command line options (#621) ([#621](https://github.com/AcademySoftwareFoundation/OpenRV/pull/621))

### 712

- Adapt build to latest MSYS2 release (#713) ([#713](https://github.com/AcademySoftwareFoundation/OpenRV/pull/713))

### 717

- Fix OUTPUT path of windows openssl cmake custom command (#734) ([#734](https://github.com/AcademySoftwareFoundation/OpenRV/pull/734))

### 746

- fix issue with with new OCIOIPNode optimisations and viewing in stack mode. (#747) ([#747](https://github.com/AcademySoftwareFoundation/OpenRV/pull/747))

### 828

- Remove Q shortcut from rvui.mu (#844) ([#844](https://github.com/AcademySoftwareFoundation/OpenRV/pull/844))

### Bug Fixes

- Update markdownlint to latest version (#1148) ([#1148](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1148))
- SG-42144: Fix off-by-one frame count error for audio-only files (#1068) ([#1068](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1068))
- Fix crashes when calling sourcesAtFrame when clearing (#1122) ([#1122](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1122))

### Build System

- Speed up builds with ccahe/scache (#1123) ([#1123](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1123))

### GitHub Actions

- use gitcliff instead of release-please (#40)
- Add semantic versioning for OpenRV to automate change logs and release (#1143) ([#1143](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1143))

### Feature/Qt6

- Fix broken Desktop Presentation Device for all platforms (#736)

### Fix

- Use RV's python version to build wheels (#1009) ([#1009](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1009))

### Qt6

- fix opengl and "C" locale warning on macOS (#771) ([#771](https://github.com/AcademySoftwareFoundation/OpenRV/pull/771))
- Disable stereo shutter glass support  (#764) ([#764](https://github.com/AcademySoftwareFoundation/OpenRV/pull/764))
- Set correct locale before Qt gets a chance to complain about it … (#702)

### RVLinkLauncher

- Custom URL Scheme Handler for OpenRV (#896) ([#896](https://github.com/AcademySoftwareFoundation/OpenRV/pull/896))

### SG-36871

- Add missing RVNode properties to documentation (#740) ([#740](https://github.com/AcademySoftwareFoundation/OpenRV/pull/740))

### SG-37377

- Add Compare to Live Review (#738) ([#738](https://github.com/AcademySoftwareFoundation/OpenRV/pull/738))

### SG-37413

- Update BMD DeckLink SDK to 15.0 (#925) ([#925](https://github.com/AcademySoftwareFoundation/OpenRV/pull/925))

### SG-38044

- Add stand-alone hold and ghost (#793) ([#793](https://github.com/AcademySoftwareFoundation/OpenRV/pull/793))

### SG-38113

- Add stand-alone Clear All Frames (#801) ([#801](https://github.com/AcademySoftwareFoundation/OpenRV/pull/801))

### SG-38658

- Add clang-tidy instructions in README.md (#742) ([#742](https://github.com/AcademySoftwareFoundation/OpenRV/pull/742))

### SG-38731

- Update annotation tool's undo/redo and clear to match Live Review's behaviour (#748) ([#748](https://github.com/AcademySoftwareFoundation/OpenRV/pull/748))

### SG-38881

- Refactor Hold and Ghost OTIO schema (#871) ([#871](https://github.com/AcademySoftwareFoundation/OpenRV/pull/871))

### SG-39280

- Update UI on Hold and Ghost in RV session (#807) ([#807](https://github.com/AcademySoftwareFoundation/OpenRV/pull/807))

### SG-39342

- Fix Screening Room Ghost Annotations (#804) ([#804](https://github.com/AcademySoftwareFoundation/OpenRV/pull/804))

### SG-39413

- Add BMD SDI support for 120Hz (#813) ([#813](https://github.com/AcademySoftwareFoundation/OpenRV/pull/813))

### SG-39419

- Disable auto mark for participants of a Live Review session (#819) ([#819](https://github.com/AcademySoftwareFoundation/OpenRV/pull/819))

### SG-39445

- Enable participants to broadcast annotations in Collaborative mode for OTIO-based Live Review sessions (#960) ([#960](https://github.com/AcademySoftwareFoundation/OpenRV/pull/960))

### SG-39476

- Refactor Hold and Ghost as session wide properties (#825) ([#825](https://github.com/AcademySoftwareFoundation/OpenRV/pull/825))

### SG-39510

- Close annotation panel when joining Live Review (#852) ([#852](https://github.com/AcademySoftwareFoundation/OpenRV/pull/852))
- Block options for Live Review participants (#834) ([#834](https://github.com/AcademySoftwareFoundation/OpenRV/pull/834))

### SG-39525

- Prevent some Rv commands from flooding the live review event queue (#835) ([#835](https://github.com/AcademySoftwareFoundation/OpenRV/pull/835))

### SG-39535

- Update UI Live Review (#829) ([#829](https://github.com/AcademySoftwareFoundation/OpenRV/pull/829))

### SG-39544

- Fix Angular Mask Pivot Value on Compare (#832) ([#832](https://github.com/AcademySoftwareFoundation/OpenRV/pull/832))

### SG-39547

- Update clang-format to 140 chars per line (#978) ([#978](https://github.com/AcademySoftwareFoundation/OpenRV/pull/978))

### SG-39640

- Add fast conversion for ProRes 4444 with alpha (#837) ([#837](https://github.com/AcademySoftwareFoundation/OpenRV/pull/837))

### SG-39680

- Fixed crash on exit with registered imgui callback (temp patch) (#836) ([#836](https://github.com/AcademySoftwareFoundation/OpenRV/pull/836))

### SG-39787

- Modernize Open RV stylesheet + Add Theme Generator (#878) ([#878](https://github.com/AcademySoftwareFoundation/OpenRV/pull/878))

### SG-39830

- Add refreshOutputVideoDevice to CommandsModule (#863) ([#863](https://github.com/AcademySoftwareFoundation/OpenRV/pull/863))

### SG-39832

- Block Zoom and Pan to participants of Live Review (#855) ([#855](https://github.com/AcademySoftwareFoundation/OpenRV/pull/855))

### SG-39876

- Block Annotation Panel in Live Review (#856) ([#856](https://github.com/AcademySoftwareFoundation/OpenRV/pull/856))

### SG-39966

- Fix annotation color selection (#877) ([#877](https://github.com/AcademySoftwareFoundation/OpenRV/pull/877))

### SG-39984

- Fix duration and startFrame paint properties (#868) ([#868](https://github.com/AcademySoftwareFoundation/OpenRV/pull/868))

### SG-40023

- Fix Clone Sync (#873) ([#873](https://github.com/AcademySoftwareFoundation/OpenRV/pull/873))

### SG-40180

- Fix rendering anomalies of concurrent paint strokes (#957) ([#957](https://github.com/AcademySoftwareFoundation/OpenRV/pull/957))

### SG-40182

- Mu event categorizations (#945) ([#945](https://github.com/AcademySoftwareFoundation/OpenRV/pull/945))

### SG-40184

- Cancel clear if plugin refuses (#961) ([#961](https://github.com/AcademySoftwareFoundation/OpenRV/pull/961))

### SG-40198

- Prep work for testing automation of concurrent annotations (#895) ([#895](https://github.com/AcademySoftwareFoundation/OpenRV/pull/895))

### SG-40348

- Fix print crashing when called from non-main thread; add warning for other mu commands (#907) ([#907](https://github.com/AcademySoftwareFoundation/OpenRV/pull/907))

### SG-40369

- SequenceNode Stability Improvements (#848) ([#848](https://github.com/AcademySoftwareFoundation/OpenRV/pull/848))

### SG-40370

- Fix Y-Inverted Color Picker (#849) ([#849](https://github.com/AcademySoftwareFoundation/OpenRV/pull/849))

### SG-40371

- Presentation Mode Enhancements (#850) ([#850](https://github.com/AcademySoftwareFoundation/OpenRV/pull/850))

### SG-40372

- Add Basic File Operations to the RVFileDialog (#851) ([#851](https://github.com/AcademySoftwareFoundation/OpenRV/pull/851))

### SG-40373

- Alt+Shift key up doesn't clear Alt modifier (#879) (#880) ([#880](https://github.com/AcademySoftwareFoundation/OpenRV/pull/880))

### SG-40385

- Better prompt, aliases and command-line environment for building rv (#913) ([#913](https://github.com/AcademySoftwareFoundation/OpenRV/pull/913))

### SG-40392

- Fix Presentation mode's Pointer option issue on High-DPI monitors (#1048) ([#1048](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1048))

### SG-40506

- Add space between option and arrow and make cmake detect qss changes (#1058) ([#1058](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1058))

### SG-40514

- Add env var to bypass Clear All confirmation dialog (#1017) ([#1017](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1017))

### SG-40541

- fix alignment glitch with QAlertPanel (#962) ([#962](https://github.com/AcademySoftwareFoundation/OpenRV/pull/962))
- fix broken qmessagebox on qt 6.5+ on macOS Tahoe with new QAlertPanel (#933) ([#933](https://github.com/AcademySoftwareFoundation/OpenRV/pull/933))

### SG-40579

- Add GIF support (#928) ([#928](https://github.com/AcademySoftwareFoundation/OpenRV/pull/928))

### SG-40626

- Garbage returned by Mu's exception handling if returning value inside catch block (#941) ([#941](https://github.com/AcademySoftwareFoundation/OpenRV/pull/941))

### SG-40730

- Fix annotations on Wacom Intuos Pro (#948) ([#948](https://github.com/AcademySoftwareFoundation/OpenRV/pull/948))

### SG-40829

- Better about box (#1000) ([#1000](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1000))

### SG-40852

- Improve paint speed degrading as you draw many annotations (#984) ([#984](https://github.com/AcademySoftwareFoundation/OpenRV/pull/984))

### SG-40855

- Auto closing panel based on event and adding an overlay that cover the whole application when needed (#971) ([#971](https://github.com/AcademySoftwareFoundation/OpenRV/pull/971))

### SG-40929

- Continued fixes based on QA. (#963) ([#963](https://github.com/AcademySoftwareFoundation/OpenRV/pull/963))

### SG-41029

- Fix crash on exception (#974) ([#974](https://github.com/AcademySoftwareFoundation/OpenRV/pull/974))

### SG-41101

- Fix crash canceling quicktime export (#986) ([#986](https://github.com/AcademySoftwareFoundation/OpenRV/pull/986))

### SG-41117

- cmake use cy files for dependency versions and add experimental support CY2025 and CY2026 (#985) ([#985](https://github.com/AcademySoftwareFoundation/OpenRV/pull/985))

### SG-41170

- Restore QMessageBox as the alertPanel() cmd implementation (#992) ([#992](https://github.com/AcademySoftwareFoundation/OpenRV/pull/992))

### SG-41173

- Add uuid and soft_deleted properties for OTIO-based Live Review (#1021) ([#1021](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1021))

### SG-41182

- Add id to Paint OTIO schema (#999) ([#999](https://github.com/AcademySoftwareFoundation/OpenRV/pull/999))

### SG-41208

- Add softDeleted paint node property to support undo, redo and clear actions in Live Review (#1027) ([#1027](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1027))

### SG-41210

- Add a per user undo-redo stack to Annotate Mode (#1016) ([#1016](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1016))

### SG-41220

- Add -update option to rvpkg command line tool (#1120) ([#1120](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1120))

### SG-41334

- Silence skipping qeventpoint message from qt (#1015) ([#1015](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1015))

### SG-41513

- Prevent tiff build from depending on libzstd (-Dzstd=OFF) (#1024) ([#1024](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1024))

### SG-41531

- Fix warning for non-transcoded media (#1079) ([#1079](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1079))

### SG-41606

- Create new softDeleted property if it doesn't exist yet (#1046) ([#1046](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1046))

### SG-41614

- Fix session manager inputs lists selection (#1055) ([#1055](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1055))

### SG-41669

- Make buttons display text instead of missing icons (#1062) ([#1062](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1062))

### SG-41715

- Send internal event on about to show menu (#1065) ([#1065](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1065))

### SG-41742

- Fix Annotation hook (#1067) ([#1067](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1067))

### SG-41787

- Add undo/redo/clear UI update event for Live Review (#1070) ([#1070](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1070))

### SG-41837

- Improve Clear All Paint (#1074) ([#1074](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1074))

### SG-41889

- add waitForProgressiveLoading() RV Command (#1094) ([#1094](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1094))

### SG-41892

- Prevent play on click in lr collab mode (#1085) ([#1085](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1085))

### SG-41909

- Fix Continuous playback annotations (#1089) ([#1089](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1089))

### SG-41927

- Fix Player won't update in opacity or wipe compare mode (#1116) ([#1116](https://github.com/AcademySoftwareFoundation/OpenRV/pull/1116))

### SG-None

- Fix typo (asyn -> async) (#908) ([#908](https://github.com/AcademySoftwareFoundation/OpenRV/pull/908))

### [444

- Add _install directory to .gitignore] (#445) ([#445](https://github.com/AcademySoftwareFoundation/OpenRV/pull/445))

