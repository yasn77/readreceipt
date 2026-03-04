// Extra JavaScript for Read Receipt Documentation

// Add custom functionality here

// Analytics tracking (if needed)
// Uncomment and configure with your analytics ID
/*
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'GA-TRACKING-ID');
*/

// Custom event tracking
document.addEventListener('DOMContentLoaded', function() {
  // Track outbound links
  const outboundLinks = document.querySelectorAll('a[href^="http"]');
  outboundLinks.forEach(function(link) {
    link.addEventListener('click', function(event) {
      const href = this.getAttribute('href');
      console.log('Outbound link clicked:', href);
      // Add your analytics tracking here
    });
  });

  // Add copy feedback for code blocks
  const codeBlocks = document.querySelectorAll('.highlight');
  codeBlocks.forEach(function(block) {
    const copyButton = block.querySelector('.md-clipboard');
    if (copyButton) {
      copyButton.addEventListener('click', function() {
        // Add visual feedback
        this.classList.add('md-clipboard--active');
        setTimeout(() => {
          this.classList.remove('md-clipboard--active');
        }, 2000);
      });
    }
  });
});

// MathJax configuration (if using math)
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: "tex2jax_ignore|searchbox",
    processHtmlClass: "tex2jax_process|mathjax"
  }
};

// Service Worker registration (for PWA support in future)
if ('serviceWorker' in navigator) {
  // Uncomment when implementing PWA
  // navigator.serviceWorker.register('/sw.js');
}

// Custom search functionality enhancements
document$.subscribe(function() {
  // Add any search-related enhancements here
  const searchInput = document.querySelector('[data-md-component="search-query"]');
  if (searchInput) {
    searchInput.addEventListener('focus', function() {
      this.parentElement.classList.add('md-search--focused');
    });
    searchInput.addEventListener('blur', function() {
      this.parentElement.classList.remove('md-search--focused');
    });
  }
});

// Table of contents improvements
document$.subscribe(function() {
  const toc = document.querySelector('.md-sidebar--secondary');
  if (toc) {
    // Highlight active section in TOC
    const headings = document.querySelectorAll('h2, h3');
    const tocLinks = toc.querySelectorAll('.md-nav__link');

    window.addEventListener('scroll', function() {
      let current = '';
      headings.forEach(function(heading) {
        const sectionTop = heading.offsetTop;
        if (window.pageYOffset >= sectionTop - 100) {
          current = heading.getAttribute('id');
        }
      });

      tocLinks.forEach(function(link) {
        link.classList.remove('md-nav__link--active');
        if (link.getAttribute('href') === '#' + current) {
          link.classList.add('md-nav__link--active');
        }
      });
    });
  }
});
