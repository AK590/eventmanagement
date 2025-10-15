document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = "http://localhost:8000/api";

    // --- State & Elements ---
    const state = {
        events: [],
        sponsors: [],
    };

    const selectors = {
        // Buttons
        showCreateModalBtn: '#showCreateEventModalBtn',
        showVerifyModalBtn: '#showVerifyModalBtn',
        addTierBtn: '#addTierBtn',
        randomizeSeatsBtn: '#randomizeSeatsBtn',
        // Modals
        modalBackdrop: '#modalBackdrop',
        createEventModal: '#createEventModal',
        infoModal: '#infoModal',
        bookingsModal: '#bookingsModal',
        // Forms & Containers
        createEventForm: '#createEventForm',
        eventsGrid: '#eventsGrid',
        tiersContainer: '#tiersContainer',
        sponsorsContainer: '#sponsorsContainer',
        toastContainer: '#toastContainer',
        bookingsModalTitle: '#bookingsModalTitle',
        bookingsModalContent: '#bookingsModalContent',
        // Templates
        eventCardTemplate: '#eventCardTemplate',
    };

    const elements = Object.keys(selectors).reduce((acc, key) => {
        acc[key] = document.querySelector(selectors[key]);
        return acc;
    }, {});
    
    // --- API Client ---
    const api = {
        async request(endpoint, options = {}) {
            const { method = 'GET', body = null, headers = {} } = options;
            const config = {
                method,
                headers: { 'Content-Type': 'application/json', ...headers },
            };
            if (body) config.body = JSON.stringify(body);

            try {
                const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'An unknown error occurred');
                }
                return response.status !== 204 ? await response.json() : null;
            } catch (error) {
                console.error(`API Error on ${method} ${endpoint}:`, error);
                showToast(error.message, 'error');
                throw error;
            }
        },
        getEvents: () => api.request('/events'),
        createEvent: (data) => api.request('/events', { method: 'POST', body: data }),
        deleteEvent: (id) => api.request(`/events/${id}`, { method: 'DELETE' }),
        createSponsor: (data) => api.request('/sponsors', { method: 'POST', body: data }),
        getSponsors: () => api.request('/sponsors'),
        getBookings: (eventId) => api.request(`/events/${eventId}/bookings`),
        bookTicket: (data) => api.request('/book', { method: 'POST', body: data }),
        verifyTicket: (hash) => api.request(`/verify/${hash}`),
        getPrice: (data) => api.request('/events/price', { method: 'POST', body: data }),
    };

    // --- UI Components & Utilities ---
    const showToast = (message, type = 'success') => {
        const toastColors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        };
        const toast = document.createElement('div');
        toast.className = `toast text-white px-6 py-3 rounded-lg shadow-lg transform translate-y-10 opacity-0 ${toastColors[type]}`;
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);
        
        setTimeout(() => toast.classList.remove('translate-y-10', 'opacity-0'), 10);
        setTimeout(() => {
            toast.classList.add('opacity-0');
            toast.addEventListener('transitionend', () => toast.remove());
        }, 5000);
    };

    const openModal = (modal) => {
        elements.modalBackdrop.classList.remove('hidden');
        modal.classList.remove('hidden');
    };

    const closeModal = (modal) => {
        elements.modalBackdrop.classList.add('hidden');
        modal.classList.add('hidden');
    };

    const formatDate = (isoString) => {
        if (!isoString) return 'Date not set';
        return new Date(isoString).toLocaleString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit'
        });
    };
    
    // --- Render Functions ---
    const renderSponsors = () => {
        elements.sponsorsContainer.innerHTML = state.sponsors.map(sponsor => `
            <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" value="${sponsor.id}" class="sponsor-checkbox">
                <span>${sponsor.name}</span>
            </label>
        `).join('') + `
            <button type="button" id="showAddSponsorFormBtn" class="text-indigo-600 font-semibold text-sm">+ Add New</button>
        `;
    };

    const renderEvents = () => {
        elements.eventsGrid.innerHTML = '';
        if (state.events.length === 0) {
            elements.eventsGrid.innerHTML = '<p class="text-center col-span-full">No upcoming events found. Create one to get started!</p>';
            return;
        }

        state.events.forEach(event => {
            const card = elements.eventCardTemplate.content.cloneNode(true);
            
            card.querySelector('.event-title').textContent = event.title;
            card.querySelector('.description').textContent = event.description || 'No description provided.';
            card.querySelector('.event-time').textContent = `${formatDate(event.start_time)} - ${formatDate(event.end_time)}`;
            card.querySelector('.total-collection').textContent = event.total_collection.toFixed(2);
            
            const sponsorsList = card.querySelector('.sponsors-list');
            if(event.sponsors && event.sponsors.length > 0) {
                sponsorsList.innerHTML = `<p class="text-xs text-gray-500">Sponsored by: ${event.sponsors.map(s => s.name).join(', ')}</p>`;
            }

            const tiersContainer = card.querySelector('.tiers-container');
            event.tiers.forEach(tier => {
                const tierDiv = document.createElement('div');
                tierDiv.className = 'tier-booking-area';
                const availableSeats = tier.total_seats - tier.seats_sold;
                tierDiv.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-semibold">${tier.name} (₹${tier.price.toFixed(2)})</span>
                        <span class="text-sm text-gray-500">${availableSeats} / ${tier.total_seats} left</span>
                    </div>
                    <div class="flex gap-2 mt-2">
                        <input class="qty border rounded-lg p-2 w-full" type="number" value="1" min="1" max="${availableSeats}" ${availableSeats === 0 ? 'disabled' : ''}>
                        <button class="bookBtn bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg font-semibold w-full" data-tier-id="${tier.id}" ${availableSeats === 0 ? 'disabled' : ''}>
                            ${availableSeats === 0 ? 'Sold Out' : 'Book'}
                        </button>
                    </div>
                `;
                tiersContainer.appendChild(tierDiv);
            });
            
            card.querySelector('.deleteBtn').addEventListener('click', () => handleDeleteEvent(event.id, event.title));
            card.querySelector('.view-bookings-btn').addEventListener('click', () => handleViewBookings(event.id, event.title));

            tiersContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('bookBtn')) {
                    const tierId = e.target.dataset.tierId;
                    const qtyInput = e.target.previousElementSibling;
                    handleBookTicket(event.id, tierId, qtyInput);
                }
            });
            
            elements.eventsGrid.appendChild(card);
        });
    };
    
    // --- Event Handlers & Logic ---
    const initializeApp = async () => {
        try {
            const [events, sponsors] = await Promise.all([api.getEvents(), api.getSponsors()]);
            state.events = events;
            state.sponsors = sponsors;
            renderEvents();
            renderSponsors();
        } catch (error) {
            elements.eventsGrid.innerHTML = '<p class="text-center col-span-full text-red-500">Could not load event data.</p>';
        }
    };
    
    const handleCreateEvent = async (e) => {
        e.preventDefault();
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        const tiers = Array.from(document.querySelectorAll('#tiersContainer .tier-group')).map(group => ({
            name: group.querySelector('.tier-name').value,
            price: parseFloat(group.querySelector('.tier-price').value),
            total_seats: parseInt(group.querySelector('.tier-seats').value),
        })).filter(t => t.name && t.price && t.total_seats);

        const totalTierSeats = tiers.reduce((sum, tier) => sum + tier.total_seats, 0);
        const totalEventSeats = parseInt(form.elements.total_seats_for_event.value);

        if (totalTierSeats !== totalEventSeats) {
            showToast('The sum of seats in all tiers must equal the total seats for the event.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Event';
            return;
        }
        
        const sponsor_ids = Array.from(document.querySelectorAll('.sponsor-checkbox:checked')).map(cb => parseInt(cb.value));

        const eventData = {
            title: form.elements.title.value,
            description: form.elements.description.value,
            location: form.elements.location.value,
            start_time: form.elements.start_time.value,
            end_time: form.elements.end_time.value,
            tiers,
            sponsor_ids,
        };

        try {
            await api.createEvent(eventData);
            showToast('Event created successfully!', 'success');
            closeModal(elements.createEventModal);
            form.reset();
            elements.tiersContainer.innerHTML = '';
            initializeApp();
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Event';
        }
    };

    const handleDeleteEvent = (eventId, eventTitle) => {
        const title = 'Confirm Deletion';
        const content = `<p>Are you sure you want to delete the event "<strong>${eventTitle}</strong>"? This action cannot be undone.</p>`;
        const actions = `
            <button class="close-modal-btn bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">Cancel</button>
            <button id="confirmDeleteBtn" class="bg-red-600 text-white px-4 py-2 rounded-lg">Delete</button>
        `;
        showInfoModal(title, content, actions);
        document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
            await api.deleteEvent(eventId);
            showToast('Event deleted successfully.', 'info');
            closeModal(elements.infoModal);
            initializeApp();
        });
    };

    const handleViewBookings = async (eventId, eventTitle) => {
        elements.bookingsModalTitle.textContent = eventTitle;
        elements.bookingsModalContent.innerHTML = `<p class="text-center p-4">Loading bookings...</p>`;
        openModal(elements.bookingsModal);

        try {
            const bookings = await api.getBookings(eventId);
            if (bookings.length === 0) {
                elements.bookingsModalContent.innerHTML = `<p class="text-center p-4">No bookings found for this event yet.</p>`;
                return;
            }

            elements.bookingsModalContent.innerHTML = `
                <table class="w-full text-left table-auto">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="px-4 py-2">Phone Number</th>
                            <th class="px-4 py-2">Tier</th>
                            <th class="px-4 py-2">Qty</th>
                            <th class="px-4 py-2">Ticket Hash</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.map(b => `
                            <tr class="border-b">
                                <td class="px-4 py-2">${b.user_phone}</td>
                                <td class="px-4 py-2">${b.tier_name}</td>
                                <td class="px-4 py-2">${b.qty}</td>
                                <td class="px-4 py-2 font-mono text-xs">${b.ticket_hash}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (error) {
            elements.bookingsModalContent.innerHTML = `<p class="text-center p-4 text-red-500">Failed to load bookings.</p>`;
        }
    };
    
    const handleBookTicket = (eventId, tierId, qtyInput) => {
        const qty = parseInt(qtyInput.value);
        if (qty <= 0) {
            showToast('Please enter a valid quantity.', 'error');
            return;
        }
        const title = 'Enter Your Phone Number';
        const content = `<p class="mb-2">Please enter your 10-digit phone number to complete the booking.</p>
                       <input id="phoneInput" type="tel" pattern="\\d{10}" maxlength="10" class="p-2 border rounded-lg w-full" placeholder="1234567890" required>`;
        const actions = `
            <button class="close-modal-btn bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
            <button id="confirmBookBtn" class="bg-green-600 text-white px-4 py-2 rounded-lg">Confirm Booking</button>
        `;
        showInfoModal(title, content, actions);
        document.getElementById('confirmBookBtn').addEventListener('click', async (e) => {
            const phone = document.getElementById('phoneInput').value;
            if (!/^\d{10}$/.test(phone)) {
                showToast('Please enter a valid 10-digit phone number.', 'error');
                return;
            }
            e.target.disabled = true;
            e.target.textContent = 'Booking...';
            try {
                const result = await api.bookTicket({ user_phone: phone, event_id: eventId, tier_id: tierId, qty });
                closeModal(elements.infoModal);
                showBookingSuccess(result);
                initializeApp();
            } catch (error) {
                 e.target.disabled = false;
                 e.target.textContent = 'Confirm Booking';
            }
        });
    };

    const handleVerifyTicket = async () => {
        const hash = document.getElementById('verifyHashInput').value.trim();
        if (!hash) {
            showToast('Please enter a ticket hash.', 'error');
            return;
        }
        try {
            const details = await api.verifyTicket(hash);
            closeModal(elements.infoModal);
            const title = `✅ Ticket Verified!`;
            const content = `
                <ul class="space-y-2">
                    <li><strong>Event:</strong> ${details.event_title}</li>
                    <li><strong>Phone:</strong> ${details.user_phone}</li>
                    <li><strong>Tickets:</strong> ${details.qty}</li>
                    <li class="font-mono text-xs pt-2"><strong>Hash:</strong> ${details.ticket_hash}</li>
                </ul>`;
            showInfoModal(title, content, '<button class="close-modal-btn bg-blue-600 text-white px-4 py-2 rounded-lg">Close</button>');
        } catch(error) {
            showToast(error.message, 'error');
        }
    };
    
    const showInfoModal = (title, content, actions) => {
        document.getElementById('infoModalTitle').innerHTML = title;
        document.getElementById('infoModalContent').innerHTML = content;
        document.getElementById('infoModalActions').innerHTML = actions;
        openModal(elements.infoModal);
    };

    const showBookingSuccess = (bookingDetails) => {
        const title = '🎉 Booking Successful!';
        const content = `<p>Your ticket is confirmed! Here is your unique ticket hash. Please save it for verification.</p>
                       <div class="mt-4 p-3 bg-gray-100 rounded-lg font-mono text-center text-sm break-all">${bookingDetails.ticket_hash}</div>
                       <p class="mt-4"><strong>Final Price:</strong> ₹${bookingDetails.price_paid.toFixed(2)}</p>`;
        const actions = `<button class="close-modal-btn bg-blue-600 text-white px-4 py-2 rounded-lg">Done</button>`;
        showInfoModal(title, content, actions);
    };

    const handleSaveSponsor = async () => {
        const name = document.getElementById('newSponsorName').value;
        const website = document.getElementById('newSponsorWebsite').value;
        if (!name) {
            showToast('Sponsor name is required', 'error');
            return;
        }
        try {
            await api.createSponsor({ name, website });
            showToast('Sponsor added!', 'success');
            closeModal(elements.infoModal);
            state.sponsors = await api.getSponsors();
            renderSponsors();
        } catch (error) {}
    };

    // --- Event Listeners Setup ---
    elements.showCreateModalBtn.addEventListener('click', () => openModal(elements.createEventModal));
    elements.showVerifyModalBtn.addEventListener('click', () => {
        showInfoModal(
            'Verify Ticket',
            '<input id="verifyHashInput" placeholder="Enter ticket hash" class="p-2 border rounded-lg w-full"/>',
            `<button class="close-modal-btn bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
             <button id="confirmVerifyBtn" class="bg-blue-600 text-white px-4 py-2 rounded-lg">Verify</button>`
        );
        document.getElementById('confirmVerifyBtn').addEventListener('click', handleVerifyTicket);
    });

    elements.createEventForm.addEventListener('submit', handleCreateEvent);
    elements.addTierBtn.addEventListener('click', () => {
        const div = document.createElement('div');
        div.className = 'grid grid-cols-1 md:grid-cols-7 gap-2 tier-group';
        div.innerHTML = `
            <input type="text" placeholder="Tier Name" class="p-2 border rounded-lg tier-name md:col-span-3" value="General Admission">
            <input type="number" placeholder="Price" class="p-2 border rounded-lg tier-price md:col-span-2">
            <input type="number" placeholder="Seats" class="p-2 border rounded-lg tier-seats">
            <button type="button" class="bg-red-100 text-red-700 rounded-lg remove-tier-btn">&times;</button>
        `;
        elements.tiersContainer.appendChild(div);
    });
    
    elements.tiersContainer.addEventListener('click', e => {
        if(e.target.classList.contains('remove-tier-btn')) {
            e.target.closest('.tier-group').remove();
        }
    });

    elements.randomizeSeatsBtn.addEventListener('click', () => {
        const totalSeats = parseInt(document.getElementById('total_seats_for_event').value);
        const tierInputs = document.querySelectorAll('.tier-seats');
        if (!totalSeats || tierInputs.length === 0) {
            showToast('Please enter total seats and add at least one tier.', 'error');
            return;
        }

        let remainingSeats = totalSeats;
        const seatsPerTier = Array(tierInputs.length).fill(0);
        for (let i = 0; i < totalSeats; i++) {
            seatsPerTier[Math.floor(Math.random() * tierInputs.length)]++;
        }

        tierInputs.forEach((input, index) => {
            input.value = seatsPerTier[index];
        });
    });

    elements.sponsorsContainer.addEventListener('click', (e) => {
        if (e.target.id === 'showAddSponsorFormBtn') {
            showInfoModal(
                'Add New Sponsor',
                `<input id="newSponsorName" placeholder="Sponsor Name" class="p-2 border rounded-lg w-full mb-2" />
                 <input id="newSponsorWebsite" placeholder="Sponsor Website (Optional)" class="p-2 border rounded-lg w-full" />`,
                `<button class="close-modal-btn bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
                 <button id="saveSponsorBtn" class="bg-blue-600 text-white px-4 py-2 rounded-lg">Save Sponsor</button>`
            );
            document.getElementById('saveSponsorBtn').addEventListener('click', handleSaveSponsor);
        }
    });

    document.body.addEventListener('click', e => {
        if (e.target.classList.contains('close-modal-btn')) {
            closeModal(e.target.closest('.modal'));
        }
    });
    
    // --- App Initialization ---
    initializeApp();
});

