# Puppy50 v98: actual NetSurf JS framebuffer breakthrough

Experiment: November 3, 2026. **This is a browser session benchmark, not a complete 384 MiB RAM-only OS.**

## Real results

JavaScript enabled in both NetSurf 3.11-2 frontends, same isolated Debian 13 environment and Xvfb 800×600, each browser run as unprivileged user and measured by same-user process PSS.

| Site | GTK PSS | Framebuffer PSS |
|---|---:|---:|
| Basic JavaScript fixture | 104.31 MiB | **24.79 MiB** |
| Wikipedia public HTTPS | 120.38 MiB | **38.59 MiB** |

Both frontends visibly executed the basic `document.write()` script and graphically loaded genuine Wikipedia via HTTPS. NetSurf-fb's Wikipedia JS also logged syntax errors, reflecting limited modern web support. The webpage screenshot exists in the workflow artifact and was independently reviewed.

These data exclude Xvfb's memory, kernel, full root filesystem, Wi-Fi firmware and other OS background services. Single-run results; no confidence interval or 384 MiB boot claim. They demonstrate meaningful savings from removing GTK, not modern JavaScript compatibility.

## Follow-up and design decision

- **Puppy50 Lite:** develop direct framebuffer/console NetSurf-fb with partial JS and the smallest maintained network stack. Verify actual RAM-only boot at 384 MiB and websites with valid certificates in QEMU and on real hardware.
- **Puppy50 Modern:** keep the verified Firefox ESR Live ISO for JavaScript-intensive applications on higher-memory hardware.
- WPE WebKit 2.54.2 compiled, but its normal user-namespace sandbox could not run in GitHub Docker; no valid headless WPE memory result. Do NOT disable its sandbox to manufacture a low-memory benchmark.

## Reproduce experimentally on X11

```bash
sudo apt install netsurf-fb
netsurf-fb --enable_javascript=1 -f x -w 760 -h 560 -b 32 https://www.wikipedia.org/
```

NetSurf JavaScript is incomplete: v96 confirmed `document.write` and DOM `innerHTML` worked, but an ES2015 arrow-function fixture raised `SyntaxError` and `fetch()` raised `ReferenceError`.

Evidence:
- [v98 GitHub Actions real screenshots + PSS](https://github.com/74127418528426leo-del/Test/actions/runs/41744398882)
- [v96 NetSurf JS ON/OFF experiments](https://github.com/74127418528426leo-del/Test/actions/runs/41743039698)
- [NetSurf official JS caveat](https://www.netsurf-browser.org/documentation/info)
- [NetSurf framebuffer port](https://www.netsurf-browser.org/about/)

Do not use this experimental browser to handle sensitive accounts until security and compatibility have been audited.
