# Full Page Screenshot Guide

Detailed workflows for capturing entire scrollable pages.

## Basic Full Page Screenshot

```
1. browser_screenshot(fullPage: true, type: "jpeg")
```

## Complete Workflow (Handles Lazy-Load + Popups)

```
1. browser_navigate(url: "https://example.com")
2. browser_wait_for(time: 2)  // Initial load
3. // Close cookie popup (see SKILL.md Section 5)
4. // Scroll to load lazy content
5. browser_evaluate(function: "async () => {
     const delay = ms => new Promise(r => setTimeout(r, ms));
     let prevHeight = -1;
     for (let i = 0; i < 30; i++) {
       window.scrollBy(0, 500);
       await delay(300);
       const newHeight = document.body.scrollHeight;
       if (newHeight === prevHeight) break;
       prevHeight = newHeight;
     }
     window.scrollTo(0, 0);
   }")
6. browser_wait_for(time: 1)  // Final settle
7. browser_screenshot(fullPage: true, type: "jpeg")
```

## Handling Fixed/Sticky Headers

Fixed and sticky headers repeat at each viewport boundary in full page screenshots.

```
1. browser_evaluate(function: "() => {
     // Remove position:fixed/sticky to prevent header repeating in screenshot
     document.querySelectorAll('header, nav, [class*=\"sticky\"], [class*=\"fixed\"]')
       .forEach(el => {
         el.style.position = 'relative';
       });
   }")
2. browser_screenshot(fullPage: true, type: "jpeg")
```

## Scroll Strategies for Lazy-Loaded Content

### Scroll to Bottom (Simple)

```
1. browser_evaluate(function: "() => window.scrollTo(0, document.body.scrollHeight)")
2. browser_wait_for(time: 1)
3. browser_snapshot()
```

### Scroll Incrementally (For Lazy-Load Images)

```
1. browser_evaluate(function: "async () => {
     const delay = ms => new Promise(r => setTimeout(r, ms));
     const maxScrolls = 50;
     let prevHeight = -1;
     for (let i = 0; i < maxScrolls; i++) {
       window.scrollBy(0, 400);
       await delay(200);
       if ((window.scrollY + window.innerHeight) >= document.body.scrollHeight) break;
     }
     window.scrollTo(0, 0);  // Return to top for screenshot
   }")
```

### Using Keyboard (End Key)

```
1. browser_press_key(key: "End")
2. browser_wait_for(time: 1)
3. browser_press_key(key: "Home")  // Return to top
```

### Using Mouse Wheel

```
1. browser_evaluate(function: "() => window.scrollBy(0, 400)")
2. browser_wait_for(time: 0.3)
3. // Repeat until bottom reached
```
