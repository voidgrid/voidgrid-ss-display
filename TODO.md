# TODO

A whole bunch of stuff in no particular order as I figure out what needs to be done.

- [x] Create config file
- [x] Make everything a function
- [x] Break functions out into a separate file
- [x] Figure out ordering things on display
- [x] Figure out groupings things
- [x] Combine image and text functionality
- [x] Write requirements.txt
- [x] Write sample systemd unit
- [x] Write sample .desktop file
- [x] Document things where human can understand it
- [x] Convert config from INI to YAML
- [x] Optimize sensor polling (TTL cache to batch psutil syscalls)
- [x] Support AMD and Intel Xe/Arc GPU temperature
- [x] Support AMD CPU temperature (k10temp, zenpower)
- [x] Harden sensor functions against unsupported hardware
- [x] Switch external IP lookup to HTTPS with timeout
- [x] Write CHANGELOG
- [x] Add CHANGELOG to README
- [x] Filter fans with 0 RPM (unplugged headers)
- [x] Add device config overrides for non-SteelSeries OLED keyboards
- [ ] Test and verify AMD GPU temperature support
- [ ] Test device config overrides against non-SteelSeries hardware

## Later: rpm and deb packages

Idea: release an rpm and a deb that also set up keyboard (HID) access, so nobody has to add the udev rule by hand.

- [ ] Replace `easyhid` with the hidapi Python binding that distros package (`python3-hidapi` on Fedora; check the Debian name), because `easyhid` is pip-only and a package cannot depend on it
- [ ] Replace `GPUtil` with a direct `nvidia-smi` call (all GPUtil does), for the same reason; this also drops the `setuptools` requirement
- [ ] Stop reading `config.yaml`, fonts and the image from the script's own directory: code and assets under `/usr/share` or `/usr/lib`, config in `/etc` or `~/.config`
- [ ] Ship the udev rule in `/usr/lib/udev/rules.d/70-ss-display.rules` and reload udev in the post-install step
- [ ] Ship the user unit in `/usr/lib/systemd/user/`
- [ ] Build both formats from one `nfpm` config with a local script (no CI); a spec file and `debian/` directory only if it should go to COPR or an apt repo
- [ ] Attach the rpm and deb to a GitHub release; signed dnf/apt repos would be a separate, larger step
- [ ] Test the rpm on Fedora and the deb in a Debian or Ubuntu container, and the HID library swap on the real keyboard
