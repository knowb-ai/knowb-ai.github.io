// Orbit carousel: one full-width cabinet at a time, travelled with the arrows,
// the mission-path stops, swipes, or the arrow keys. Travelling narrows the
// current cabinet shut and widens the next one open; each cabinet's brief folds
// into a drawer that opens smoothly. Without this script every cabinet is
// listed in full.
(function () {
    var motion = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var CLOSE_MS = 280;
    var OPEN_MS = 420;

    function setDrawer(slide, open) {
        var drawer = slide.querySelector('.cabinet-more');
        var toggle = slide.querySelector('.cabinet-more-toggle');
        if (!drawer || !toggle) return;
        drawer.classList.toggle('is-open', open);
        drawer.inert = !open;
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.querySelector('.cabinet-more-label').textContent = open ? 'Close brief' : 'Read full brief';
    }

    document.querySelectorAll('[data-orbit-carousel]').forEach(function (root) {
        var track = root.querySelector('.orbit-track');
        var slides = Array.prototype.slice.call(track.children);
        var stops = Array.prototype.slice.call(root.querySelectorAll('.orbit-stop'));
        var prev = root.querySelector('.orbit-prev');
        var next = root.querySelector('.orbit-next');
        var current = 0;
        var busy = false;

        function show(index) {
            slides.forEach(function (slide, i) {
                var active = i === index;
                slide.classList.toggle('is-current', active);
                slide.inert = !active;
                slide.setAttribute('aria-hidden', active ? 'false' : 'true');
            });
            stops.forEach(function (stop, i) {
                stop.setAttribute('aria-current', i === index ? 'true' : 'false');
            });
            prev.disabled = index === 0;
            next.disabled = index === slides.length - 1;
            current = index;
        }

        function go(index) {
            index = Math.max(0, Math.min(slides.length - 1, index));
            if (index === current || busy) return;
            var leaving = slides[current];
            var entering = slides[index];
            setDrawer(leaving, false);
            if (!motion) {
                show(index);
                return;
            }
            busy = true;
            leaving.classList.add('is-leaving');
            setTimeout(function () {
                leaving.classList.remove('is-leaving');
                entering.classList.add('is-entering');
                show(index);
                setTimeout(function () {
                    entering.classList.remove('is-entering');
                    busy = false;
                }, OPEN_MS);
            }, CLOSE_MS);
        }

        slides.forEach(function (slide) {
            var toggle = slide.querySelector('.cabinet-more-toggle');
            if (!toggle) return;
            toggle.hidden = false;
            setDrawer(slide, false);
            toggle.addEventListener('click', function () {
                setDrawer(slide, toggle.getAttribute('aria-expanded') !== 'true');
            });
        });

        prev.addEventListener('click', function () { go(current - 1); });
        next.addEventListener('click', function () { go(current + 1); });
        stops.forEach(function (stop, i) {
            stop.addEventListener('click', function () { go(i); });
        });
        track.addEventListener('keydown', function (event) {
            if (event.target !== track) return;
            if (event.key === 'ArrowRight') {
                event.preventDefault();
                go(current + 1);
            } else if (event.key === 'ArrowLeft') {
                event.preventDefault();
                go(current - 1);
            }
        });

        // Horizontal swipes on touch and pen travel the track.
        var startX = null;
        var startY = null;
        track.addEventListener('pointerdown', function (event) {
            if (event.pointerType === 'mouse') return;
            startX = event.clientX;
            startY = event.clientY;
        });
        track.addEventListener('pointerup', function (event) {
            if (startX === null) return;
            var dx = event.clientX - startX;
            var dy = event.clientY - startY;
            startX = null;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
                go(current + (dx < 0 ? 1 : -1));
            }
        });

        root.classList.add('is-enhanced');
        root.querySelector('.orbit-controls').hidden = false;
        current = -1;
        show(0);
    });
}());
