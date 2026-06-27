(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const receiptLines  = $('#receipt-lines');
  const receiptTotal  = $('#receipt-total');
  const receiptId     = $('#receipt-id');
  const formQuoteVal  = $('#form-quote-value');
  const bookService   = $('#book-service');
  const bookVehicle   = $('#book-vehicle');
  const bookingForm   = $('#booking-form');
  const formStatus    = $('#form-status');
  const carStage      = document.querySelector('.car-stage');

  const SERVICE_LABEL = { exterior: 'Exterior Wash & Dry', full: 'Full Detail' };
  const VEHICLE_LABEL = { sedan: 'Sedan', suv: 'SUV', truck: 'Truck', van: 'Van / Minivan' };

  let currentQuote = null;

  function getQuoteState() {
    const service = document.querySelector('input[name="service"]:checked')?.value || 'exterior';
    const vehicle = document.querySelector('input[name="vehicle"]:checked')?.value || 'sedan';
    const addons  = Array.from(document.querySelectorAll('input[name="addons"]:checked')).map(el => el.value);
    return { service, vehicle, addons };
  }

  function renderReceipt(quote) {
    currentQuote = quote;
    const lines = [];
    lines.push(`<div class="receipt-line"><span>${SERVICE_LABEL[quote.service] || quote.service}</span><span>$${quote.base.toFixed(0)}</span></div>`);
    if (quote.multiplier !== 1.0) {
      const vehicleAdj = (quote.subtotal - quote.base).toFixed(0);
      lines.push(`<div class="receipt-line"><span>${VEHICLE_LABEL[quote.vehicle] || quote.vehicle} (${quote.multiplier}×)</span><span>+$${vehicleAdj}</span></div>`);
    }
    if (quote.addons && quote.addons.length) {
      quote.addons.forEach(a => {
        lines.push(`<div class="receipt-line receipt-line-addon"><span>+ ${a.label}</span><span>$${a.price}</span></div>`);
      });
    }
    lines.push(`<div class="receipt-line receipt-line-subtotal"><span>Subtotal</span><span>$${(quote.subtotal + quote.addons_total).toFixed(0)}</span></div>`);
    receiptLines.innerHTML = lines.join('');
    receiptTotal.textContent  = '$' + Math.round(quote.total);
    formQuoteVal.textContent  = '$' + Math.round(quote.total);
    receiptId.textContent     = 'DND-' + Date.now().toString().slice(-6);
  }

  async function fetchQuote() {
    const state = getQuoteState();
    try {
      const r = await fetch('/api/quote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      });
      if (!r.ok) throw new Error('Quote request failed');
      const data = await r.json();
      renderReceipt(data);
      if (bookService.value !== state.service)  bookService.value = state.service;
      if (bookVehicle.value !== state.vehicle)  bookVehicle.value = state.vehicle;
    } catch (err) {
      console.error(err);
      receiptLines.innerHTML = '<div class="receipt-line"><span>Couldn\'t load quote</span><span>—</span></div>';
    }
  }

  $$('input[name="service"], input[name="vehicle"], input[name="addons"]').forEach(el => el.addEventListener('change', fetchQuote));

  $$('.service-select').forEach(btn => {
    btn.addEventListener('click', () => {
      const svc = btn.dataset.service;
      const radio = document.querySelector(`input[name="service"][value="${svc}"]`);
      if (radio) { radio.checked = true; fetchQuote(); }
      document.getElementById('quote').scrollIntoView({ behavior: 'smooth' });
    });
  });

  bookService.addEventListener('change', () => {
    const r = document.querySelector(`input[name="service"][value="${bookService.value}"]`);
    if (r) { r.checked = true; fetchQuote(); }
  });
  bookVehicle.addEventListener('change', () => {
    const r = document.querySelector(`input[name="vehicle"][value="${bookVehicle.value}"]`);
    if (r) { r.checked = true; fetchQuote(); }
  });

  bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    formStatus.hidden = true;
    formStatus.className = 'form-status';
    const fd = new FormData(bookingForm);
    const quoteState = getQuoteState();
    const payload = {
      name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'), address: fd.get('address'),
      service: fd.get('service'), vehicle: fd.get('vehicle'), date: fd.get('date'), time: fd.get('time'),
      notes: fd.get('notes'), addons: quoteState.addons, quoted_total: currentQuote ? currentQuote.total : null,
    };
    const missing = ['name','email','phone','address','service','vehicle','date','time'].filter(k => !payload[k]);
    if (missing.length) {
      formStatus.textContent = 'Please fill in: ' + missing.join(', ');
      formStatus.className = 'form-status form-status-error';
      formStatus.hidden = false;
      return;
    }
    try {
      const r = await fetch('/api/book', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await r.json();
      if (r.ok && data.success) {
        formStatus.innerHTML = `✓ Booked. Confirmation #${data.booking_id}. We'll email <strong>${payload.email}</strong> within an hour to lock in your time.`;
        formStatus.className = 'form-status form-status-success';
        formStatus.hidden = false;
        bookingForm.reset();
        document.querySelector('input[name="service"][value="exterior"]').checked = true;
        document.querySelector('input[name="vehicle"][value="sedan"]').checked = true;
        $$('input[name="addons"]').forEach(el => el.checked = false);
        fetchQuote();
        formStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        throw new Error(data.error || 'Booking failed');
      }
    } catch (err) {
      formStatus.textContent = 'Something went wrong: ' + err.message;
      formStatus.className = 'form-status form-status-error';
      formStatus.hidden = false;
    }
  });

  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (!carStage) return;
    carStage.classList.add('driving');
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => carStage.classList.remove('driving'), 200);
  }, { passive: true });

  const carSVG = document.querySelector('.car');
  const spongeGroup = document.querySelector('.sponge-group');
  if (carSVG && spongeGroup && carStage) {
    let leaveTimer = null;
    carSVG.addEventListener('mousemove', (e) => {
      const rect = carSVG.getBoundingClientRect();
      const svgX = ((e.clientX - rect.left) / rect.width) * 700;
      const svgY = ((e.clientY - rect.top)  / rect.height) * 280;
      carStage.classList.add('user-cleaning');
      const tilt = Math.sin(Date.now() / 120) * 6;
      spongeGroup.style.transform = `translate(${svgX}px, ${svgY}px) rotate(${tilt}deg)`;
      if (Math.random() < 0.15) spawnBubble(svgX, svgY);
      clearTimeout(leaveTimer);
    });
    carSVG.addEventListener('mouseleave', () => {
      leaveTimer = setTimeout(() => {
        carStage.classList.remove('user-cleaning');
        spongeGroup.style.transform = '';
      }, 300);
    });
    carSVG.addEventListener('touchmove', (e) => {
      const touch = e.touches[0];
      if (!touch) return;
      const rect = carSVG.getBoundingClientRect();
      const svgX = ((touch.clientX - rect.left) / rect.width) * 700;
      const svgY = ((touch.clientY - rect.top)  / rect.height) * 280;
      carStage.classList.add('user-cleaning');
      spongeGroup.style.transform = `translate(${svgX}px, ${svgY}px)`;
      if (Math.random() < 0.2) spawnBubble(svgX, svgY);
    }, { passive: true });
    carSVG.addEventListener('touchend', () => {
      setTimeout(() => {
        carStage.classList.remove('user-cleaning');
        spongeGroup.style.transform = '';
      }, 300);
    });
  }

  function spawnBubble(x, y) {
    const svgNS = 'http://www.w3.org/2000/svg';
    const bubblesGroup = document.querySelector('.bubbles');
    if (!bubblesGroup) return;
    const b = document.createElementNS(svgNS, 'circle');
    b.setAttribute('cx', x + (Math.random() - 0.5) * 30);
    b.setAttribute('cy', y + 5);
    b.setAttribute('r', 2 + Math.random() * 3);
    b.setAttribute('fill', 'rgba(255,255,255,0.8)');
    b.style.animation = 'bubble-rise 2.2s ease-out forwards';
    bubblesGroup.appendChild(b);
    setTimeout(() => b.remove(), 2300);
  }

  const dateInput = document.querySelector('input[name="date"]');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
  }

  fetchQuote();
})();
