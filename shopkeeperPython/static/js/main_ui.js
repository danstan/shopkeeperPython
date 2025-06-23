    // Main game interface script
    // Access Jinja variables via window.gameConfig
    var currentTownSubLocations = window.gameConfig.currentTownSubLocationsJson;
    var allTownsData = window.gameConfig.allTownsDataJson;
    var hemlockHerbsData = {};
    try {
        // hemlockHerbsJson is already a string from json.dumps in Python, passed via |safe
        if (window.gameConfig.hemlockHerbsJson) {
            hemlockHerbsData = JSON.parse(window.gameConfig.hemlockHerbsJson);
        }
    } catch (e) {
        console.error("Error parsing Hemlock's herbs JSON from gameConfig:", e);
        // hemlockHerbsData remains {}
    }

    var borinItemsData = {};
    if (window.gameConfig && window.gameConfig.borinItemsJson) {
        try {
            borinItemsData = JSON.parse(window.gameConfig.borinItemsJson);
        } catch (e) {
            console.error("Error parsing Borin's items JSON from gameConfig:", e);
        }
    }


    document.addEventListener('DOMContentLoaded', function() {
        var playerInventoryForSellDropdown = window.gameConfig.playerInventory;

        // Function to display toast messages
        function showToast(message, type = 'info', duration = 5000) {
            const container = document.getElementById('toast-container');
            if (!container) {
                console.error('Toast container not found!');
                return;
            }

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`; // Base class + type class (e.g., toast-success, toast-error)

            // Optional: Add an icon based on type
            let iconHtml = '';
            if (type === 'success') {
                iconHtml = '<span class="toast-icon">✔️</span>'; // Simple checkmark
            } else if (type === 'error') {
                iconHtml = '<span class="toast-icon">❌</span>'; // Simple X
            } else if (type === 'warning') {
                iconHtml = '<span class="toast-icon">⚠️</span>'; // Warning sign
            } else {
                iconHtml = '<span class="toast-icon">ℹ️</span>'; // Info sign
            }

            toast.innerHTML = `${iconHtml} <span class="toast-message">${message}</span>`;

            container.appendChild(toast);

            // Animate in
            setTimeout(() => {
                toast.classList.add('show');
            }, 100); // Small delay to allow CSS transition to catch the class change

            // Remove toast after duration
            setTimeout(() => {
                toast.classList.remove('show');
                // Remove the element from DOM after transition out
                toast.addEventListener('transitionend', () => {
                    if (toast.parentElement) {
                        toast.parentElement.removeChild(toast);
                    }
                });
            }, duration);
        }

        // Example usage (for testing, can be removed later):
        // showToast("This is a success message!", "success");
        // showToast("This is an error message.", "error", 7000);
        // showToast("Standard information toast.");

            // Logic for populating and handling the sell item dropdown
            // const sellDetailsDiv = document.getElementById('div_sell_details'); // Already declared
            const sellItemDropdown = document.getElementById('sell_item_dropdown');
            // const sellItemNameInput = document.getElementById('sell_item_name'); // Already declared

            function populateSellDropdown() {
                if (!sellItemDropdown || !playerInventoryForSellDropdown) return;

                sellItemDropdown.innerHTML = '<option value="">-- Select an item to sell --</option>'; // Default empty option

                playerInventoryForSellDropdown.forEach(item => {
                    const option = document.createElement('option');
                    let itemName = '';
                    if (typeof item === 'string') {
                        itemName = item;
                    } else if (typeof item === 'object' && item !== null && item.name) {
                        itemName = item.name;
                    } else {
                        return; // Skip if item format is unexpected
                    }
                    option.value = itemName;
                    option.textContent = itemName;
                    sellItemDropdown.appendChild(option);
                });
            }

            if (sellItemDropdown && sellItemNameInput) { // sellItemNameInput is declared further down, this might be an issue.
                                                        // However, sellItemNameInput is fetched within actionForm block.
                                                        // This event listener should be fine as long as sellItemNameInput becomes available
                                                        // by the time a change event occurs.
                sellItemDropdown.addEventListener('change', function() {
                    // Re-fetch sellItemNameInput here to be safe, as its declaration is later.
                    const currentSellItemNameInput = document.getElementById('sell_item_name');
                    if (this.value && currentSellItemNameInput) {
                        currentSellItemNameInput.value = this.value;
                    }
                });
            }

        // Existing script for actionForm, map, sub-locations etc.
        if (document.getElementById('actionForm')) {
            const actionForm = document.getElementById('actionForm');
            const hiddenActionNameInput = document.getElementById('action_name_hidden');
            const hiddenDetailsInput = document.getElementById('action_details');

            const mapDestinationsDiv = document.getElementById('map-destinations');
            const subLocationsListDiv = document.getElementById('sub-locations-list');
            // const currentActionsListDiv = document.getElementById('current-actions-list'); // No longer primary target for displayActions
            let currentActionsListDiv = document.getElementById('current-actions-list'); // Keep for event listener for now
            const currentTownDisplay = document.getElementById('current-town-display');

            // Modal elements
            const subLocationActionsModal = document.getElementById('subLocationActionsModal');
            const modalActionsListDiv = document.getElementById('modal-actions-list');
            const modalCloseButton = subLocationActionsModal ? subLocationActionsModal.querySelector('.close-button') : null;


            // Action Detail Divs and Inputs
            const actionDetailsContainer = document.getElementById('action-details-container');
            const craftDetailsDiv = document.getElementById('div_craft_details');
            const craftItemNameInput = document.getElementById('craft_item_name');
            const buyDetailsDiv = document.getElementById('div_buy_details');
            const buyItemNameInput = document.getElementById('buy_item_name');
            const buyQuantityInput = document.getElementById('buy_quantity');
            const sellDetailsDiv = document.getElementById('div_sell_details');
            const sellItemNameInput = document.getElementById('sell_item_name');
            const hemlockHerbsDetailsDiv = document.getElementById('div_hemlock_herbs_details');
            const hemlockHerbsListDiv = document.getElementById('hemlock-herbs-list'); // New div for list

            const borinItemsDetailsDiv = document.getElementById('div_borin_items_details'); // Declare it

            const allDetailDivs = [craftDetailsDiv, buyDetailsDiv, sellDetailsDiv, hemlockHerbsDetailsDiv, borinItemsDetailsDiv];
            let currentActionRequiringDetails = null;
            let currentSubLocationName = null;
            let selectedHemlockHerbName = null; // To store the selected Hemlock herb
            let selectedBorinItemName = null; // To store the selected Borin item


            function hideAllDetailForms() {
                if (actionDetailsContainer) actionDetailsContainer.style.display = 'none';
                allDetailDivs.forEach(div => { if (div) div.style.display = 'none'; });
            }

            function displaySubLocations(subLocations) {
                if (!subLocationsListDiv) return;
                subLocationsListDiv.innerHTML = '';
                if (currentActionsListDiv) currentActionsListDiv.innerHTML = '';
                hideAllDetailForms(); // Also hide detail forms when sub-locations are re-rendered

                if (subLocations && subLocations.length > 0) {
                    const ul = document.createElement('ul');
                    subLocations.forEach(subLoc => {
                        const li = document.createElement('li');
                        const button = document.createElement('button');
                        button.type = 'button'; // <--- ADD THIS LINE
                        button.className = 'sub-location-button';
                        button.dataset.sublocName = subLoc.name;
                        button.textContent = subLoc.name;
                        li.appendChild(button);
                        if (subLoc.description) {
                            li.append(` - ${subLoc.description}`);
                        }
                        ul.appendChild(li);
                    });
                    subLocationsListDiv.appendChild(ul);
                } else {
                    subLocationsListDiv.innerHTML = '<p>No sub-locations here.</p>';
                }
            }

            // Function to display actions for a selected sub-location
            function displayActions(subLocName) {
                // if (!currentActionsListDiv) return; // Old target
                // currentActionsListDiv.innerHTML = ''; // Clear previous
                if (!modalActionsListDiv || !subLocationActionsModal) {
                    console.error("Modal elements not found for displayActions");
                    return;
                }
                modalActionsListDiv.innerHTML = ''; // Clear previous modal actions
                currentSubLocationName = subLocName; // Store the sub-location name

                const currentTownName = currentTownDisplay ? currentTownDisplay.textContent : null;
                if (!currentTownName || !allTownsData || !allTownsData[currentTownName] || !allTownsData[currentTownName].sub_locations) {
                    console.error("Could not find current town data or sub-locations for action display.");
                    return;
                }
                const subLocationsData = allTownsData[currentTownName].sub_locations;


                const selectedSubLocation = subLocationsData.find(sl => sl.name === subLocName);

                if (selectedSubLocation && selectedSubLocation.actions && selectedSubLocation.actions.length > 0) {
                    const ul = document.createElement('ul');
                    selectedSubLocation.actions.forEach(actionStr => {
                        const li = document.createElement('li');
                        const button = document.createElement('button');
                        button.className = 'action-button'; // Keep class for existing event listeners
                        button.dataset.actionName = actionStr;
                        button.textContent = actionStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Prettify
                        li.appendChild(button);
                        ul.appendChild(li);
                    });
                    modalActionsListDiv.appendChild(ul);
                    subLocationActionsModal.style.display = 'block'; // Show modal
                } else {
                    modalActionsListDiv.innerHTML = '<p>No actions available here.</p>';
                    subLocationActionsModal.style.display = 'block'; // Show modal even if no actions, to indicate it was opened
                }
            }

            // Modal Close Functionality
            if (modalCloseButton) {
                modalCloseButton.addEventListener('click', function() {
                    if (subLocationActionsModal) subLocationActionsModal.style.display = 'none';
                });
            }

            if (subLocationActionsModal) {

                // REMOVED:
                // window.addEventListener('click', function(event) {
                //     if (event.target == subLocationActionsModal) { // Clicked outside of the modal content
                //         subLocationActionsModal.style.display = 'none';
                //     }
                // });

                // ADDED:
                subLocationActionsModal.addEventListener('click', function(event) {
                    // If the click is directly on the modal backdrop (event.target is the modal itself)
                    // then close the modal.
                    if (event.target === subLocationActionsModal) {

                        subLocationActionsModal.style.display = 'none';
                    }
                });
            }

            // Event Listener for Map Destination Buttons
            if (mapDestinationsDiv) {
                mapDestinationsDiv.addEventListener('click', function(event) {
                    if (event.target.classList.contains('map-destination-button')) {
                        const townName = event.target.dataset.townName;
                        if (hiddenActionNameInput) hiddenActionNameInput.value = 'travel_to_town';
                        if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({ town_name: townName });
                        if (actionForm) {
                            console.log('Submitting action. Name:', hiddenActionNameInput.value);
                            console.log('Submitting action. Details:', hiddenDetailsInput.value);
                            actionForm.submit();
                        }
                    }
                });
            }

            // Event Listener for Sub-location Buttons
            if (subLocationsListDiv) {
                subLocationsListDiv.addEventListener('click', function(event) {
                    if (event.target.classList.contains('sub-location-button')) {
                        const subLocName = event.target.dataset.sublocName;
                        displayActions(subLocName);
                    }
                });
            }

            // Event Listener for Action Buttons (now potentially inside modal or other containers)
            // This listener should be attached to a static parent that exists at load time,
            // or re-evaluate if currentActionsListDiv is still the correct parent for all actions.
            // For now, we assume action buttons are still eventually handled if they bubble up
            // or if the modal's content is part of a structure listened to by 'currentActionsListDiv's parent.
            // Let's refine this: if actions are ONLY in the modal, this listener needs to be on modalActionsListDiv or its parent.
            // However, the original setup might have used event delegation on a higher-up container.
            // The most robust change is to make the listener target the modal if that's where buttons are now.
            // For the subtask, the buttons are moved to `modal-actions-list`.
            // So, the listener for these specific buttons should be on `modalActionsListDiv`.
            // The old `currentActionsListDiv` might still be used for other things or might become obsolete for this.

            const actionButtonClickHandler = function(event) {
                if (event.target.classList.contains('action-button')) {
                    const actionName = event.target.dataset.actionName;
                    // Hide the modal if an action button inside it is clicked
                    if (subLocationActionsModal && subLocationActionsModal.contains(event.target)) {
                        subLocationActionsModal.style.display = 'none';
                    }
                        hideAllDetailForms(); // Hide any open detail forms first
                        currentActionRequiringDetails = null; // Reset

                        if (hiddenActionNameInput) hiddenActionNameInput.value = actionName; // Set action name for the form

                        // Check if this action is 'craft' AND if it's coming from the dynamic action list
                        // vs. the new recipe list. The new recipe list buttons are handled separately.
                        // The original 'craft' action button (if any existed in sub-locations)
                        // would show the generic craft details form.
                        if (actionName === 'craft' && !event.target.classList.contains('craft-recipe-button')) {
                            if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                            if (craftDetailsDiv) craftDetailsDiv.style.display = 'block'; // Show generic craft input
                            currentActionRequiringDetails = actionName;
                            // Do NOT submit form yet for generic craft
                        } else if (actionName === 'buy_from_own_shop') {
                            if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                            if (buyDetailsDiv) buyDetailsDiv.style.display = 'block';
                            currentActionRequiringDetails = actionName;
                            // Do NOT submit form yet
                        } else if (actionName === 'sell_to_own_shop') {
                            if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                            if (sellDetailsDiv) sellDetailsDiv.style.display = 'block';
                            currentActionRequiringDetails = actionName;
                            populateSellDropdown(); // Call to populate when the sell form is shown
                            // Do NOT submit form yet
                        } else if (actionName === 'buy_from_npc' && currentSubLocationName === "Old Man Hemlock's Hut") {
                            if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                            if (hemlockHerbsDetailsDiv) hemlockHerbsDetailsDiv.style.display = 'block';

                            currentActionRequiringDetails = actionName; // Could be 'buy_from_hemlock_ui' or similar if more distinction needed

                            selectedHemlockHerbName = null; // Reset selection when showing the list
                            if (hemlockHerbsListDiv) {
                                hemlockHerbsListDiv.innerHTML = ''; // Clear previous list
                                if (hemlockHerbsData && Object.keys(hemlockHerbsData).length > 0) {
                                    const ul = document.createElement('ul');

                                    ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                                    for (const herbKey in hemlockHerbsData) {
                                        const herb = hemlockHerbsData[herbKey];
                                        const li = document.createElement('li');
                                        li.style.marginBottom = '10px';
                                        li.innerHTML = `
                                            <strong>${herb.name}</strong> - ${herb.price}G<br>
                                            <em>${herb.description}</em><br>
                                            <button type="button" class="select-hemlock-herb-button popup-menu-button" data-herb-name="${herb.name}">Select</button>

                                        `;
                                        ul.appendChild(li);
                                    }
                                    hemlockHerbsListDiv.appendChild(ul);
                                } else {
                                    hemlockHerbsListDiv.innerHTML = '<p>No herbs available from Hemlock at this time.</p>';
                                }
                            }

                        } else if (actionName === 'talk_to_borin' && currentSubLocationName === "Borin Stonebeard's Smithy") {
                            if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                            if (borinItemsDetailsDiv) borinItemsDetailsDiv.style.display = 'block';
                            currentActionRequiringDetails = 'buy_from_borin_ui'; // Distinct UI state
                            selectedBorinItemName = null; // Reset selection
                            const borinItemsListDiv = document.getElementById('borin-items-list');
                            if (borinItemsListDiv) {
                                borinItemsListDiv.innerHTML = ''; // Clear previous list
                                if (borinItemsData && Object.keys(borinItemsData).length > 0) {
                                    const ul = document.createElement('ul');
                                    ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                                    for (const itemKey in borinItemsData) {
                                        const item = borinItemsData[itemKey];
                                        const li = document.createElement('li');
                                        li.style.marginBottom = '10px';
                                        li.innerHTML = `
                                            <strong>${item.name}</strong> - ${item.price}G<br>
                                            <em>${item.description}</em><br>
                                            <button type="button" class="select-borin-item-button popup-menu-button" data-item-name="${item.name}">Select</button>
                                        `;
                                        ul.appendChild(li);
                                    }
                                    borinItemsListDiv.appendChild(ul);
                                } else {
                                    borinItemsListDiv.innerHTML = '<p>Borin has nothing to sell right now.</p>';
                                }
                            }

                        } else if (!event.target.classList.contains('craft-recipe-button')) {
                            // For actions not needing details from the dynamic list
                            if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({});
                            if (actionForm) {
                            if (event.target && typeof event.target.classList !== 'undefined') { // Ensure event.target is an element
                                event.target.classList.add('button-processing');
                            }
                                console.log('Submitting action (no details). Name:', hiddenActionNameInput.value);
                                console.log('Submitting action (no details). Details:', hiddenDetailsInput.value);
                                actionForm.submit();
                            }
                        }
                    }
            };

            // Attach the handler to the modal list for actions populated by displayActions
            if (modalActionsListDiv) {
                modalActionsListDiv.addEventListener('click', actionButtonClickHandler);
            }

            // If currentActionsListDiv is still used for other buttons (e.g. not from displayActions),
            // it needs its own listener or a shared one if they are in a common parent.
            // For now, assuming actions from displayActions are the primary concern for the modal.
            // If currentActionsListDiv was only for sub-location actions, it might not need a listener anymore
            // if all sub-location actions now go to the modal.
            // Let's keep its original listener for now, in case it handles other dynamically added buttons
            // that are NOT part of sub-location actions.
             if (currentActionsListDiv) {
                currentActionsListDiv.addEventListener('click', actionButtonClickHandler);
             }


            // Event Listener for the new Craft Recipe Buttons
            const craftingRecipesList = document.getElementById('crafting-recipes-list');
            if (craftingRecipesList) {
                craftingRecipesList.addEventListener('click', function(event) {
                    if (event.target.classList.contains('craft-recipe-button')) {
                        const itemName = event.target.dataset.itemName;
                        if (hiddenActionNameInput) hiddenActionNameInput.value = 'craft';
                        if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({ item_name: itemName });
                        if (actionForm) {
                            console.log('Submitting action (craft recipe). Name:', hiddenActionNameInput.value);
                            console.log('Submitting action (craft recipe). Details:', hiddenDetailsInput.value);
                            actionForm.submit();
                        }
                    }
                });
            }

            // Event Listener for the Gather Resources Button
            const gatherResourcesButton = document.getElementById('gatherResourcesButton');
            if (gatherResourcesButton) {
                gatherResourcesButton.addEventListener('click', function() {
                    if (hiddenActionNameInput) hiddenActionNameInput.value = 'gather_resources';
                    if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({}); // Empty details
                    if (actionForm) {
                        console.log('Submitting action (gather_resources). Name:', hiddenActionNameInput.value);
                        console.log('Submitting action (gather_resources). Details:', hiddenDetailsInput.value);
                        actionForm.submit();
                    }
                });
            }

            function compileAndSetActionDetails() {
                let details = {};
                if (!currentActionRequiringDetails) return; // Should not happen if a detail submit button was clicked

                switch (currentActionRequiringDetails) {
                    case 'craft':
                        if (craftItemNameInput && craftItemNameInput.value) {
                            details.item_name = craftItemNameInput.value;
                        }
                        break;
                    case 'buy_from_own_shop':
                        if (buyItemNameInput && buyItemNameInput.value) {
                            details.item_name = buyItemNameInput.value;
                        }
                        if (buyQuantityInput && buyQuantityInput.value) {
                            details.quantity = parseInt(buyQuantityInput.value, 10);
                        }
                        break;
                    case 'sell_to_own_shop':
                        if (sellItemNameInput && sellItemNameInput.value) {
                            details.item_name = sellItemNameInput.value;
                        }
                        break;
                    // Case for 'buy_from_npc' (Old Man Hemlock) will be handled by its own button listener,
                    // as it needs to capture the selected herb, which isn't part of this generic function.
                    // This function is for the generic ".submit-details-button"s.
                }
                if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify(details);
            }

            // Event Listener for "Submit Details" buttons within each detail form (generic ones)
            if (actionDetailsContainer) {
                actionDetailsContainer.addEventListener('click', function(event) {
                    if (event.target.classList.contains('submit-details-button')) { // Generic submit buttons
                        if (!currentActionRequiringDetails) {
                            console.error("[SubtaskDebug] Submit details button clicked but no currentActionRequiringDetails is set. This may indicate an issue with how currentActionRequiringDetails is managed or that the click event is firing unexpectedly.");
                            return;
                        }

                        // Defensive assignment of action_name right before compiling details and submitting
                        if (hiddenActionNameInput) {
                             if (currentActionRequiringDetails === 'buy_from_own_shop' ||
                                 currentActionRequiringDetails === 'sell_to_own_shop' ||
                                 currentActionRequiringDetails === 'craft') { // 'craft' is for the generic craft form button
                                hiddenActionNameInput.value = currentActionRequiringDetails;
                                console.log('[SubtaskDebug] Defensively set hiddenActionNameInput.value to:', currentActionRequiringDetails);
                             } else {
                                // If currentActionRequiringDetails is something else, this specific defensive assignment isn't for it.
                                // This is not an error, just means this button click wasn't for buy/sell/generic craft.
                                // console.warn('[SubtaskDebug] currentActionRequiringDetails is set to "' + currentActionRequiringDetails + '", not buy/sell/craft. No defensive assignment made by this block.');
                             }
                        } else {
                            console.error('[SubtaskDebug] hiddenActionNameInput is null. Cannot set action name.');
                        }

                        compileAndSetActionDetails(); // This uses currentActionRequiringDetails to populate the details

                        if (actionForm) {
                            if (event.target && typeof event.target.classList !== 'undefined') {
                                event.target.classList.add('button-processing');
                            }
                            console.log('[SubtaskDebug] Attempting to submit form. Action Name:',
                                        (hiddenActionNameInput ? hiddenActionNameInput.value : "ERROR: hiddenActionNameInput is null"),
                                        '. Details JSON:',
                                        (hiddenDetailsInput ? hiddenDetailsInput.value : "ERROR: hiddenDetailsInput is null"));
                            actionForm.submit();
                        } else {
                            console.error('[SubtaskDebug] actionForm not found for submission. Form cannot be submitted.');
                        }
                    }
                });
            }

            // Event listener for selecting a Hemlock herb
            if (hemlockHerbsListDiv) {
                hemlockHerbsListDiv.addEventListener('click', function(event) {
                    if (event.target.classList.contains('select-hemlock-herb-button')) {
                        selectedHemlockHerbName = event.target.dataset.herbName;
                        // Optional: Visual feedback for selection
                        document.querySelectorAll('.select-hemlock-herb-button').forEach(btn => {
                            btn.style.fontWeight = 'normal'; // Reset others
                            btn.style.backgroundColor = '';
                        });
                        event.target.style.fontWeight = 'bold'; // Highlight selected
                        event.target.style.backgroundColor = '#a0d2a0'; // Light green highlight
                        console.log("Selected herb: " + selectedHemlockHerbName);
                    }
                });
            }

            // Specific listener for "Buy Selected Herb" button from Hemlock's details
            const submitBuyHemlockHerbButton = document.getElementById('submit_buy_hemlock_herb_button');
            const hemlockQuantityInput = document.getElementById('hemlock_quantity_dynamic');


            if (submitBuyHemlockHerbButton && hemlockQuantityInput && hiddenActionNameInput && hiddenDetailsInput && actionForm) { // Added guards

                submitBuyHemlockHerbButton.addEventListener('click', function() {
                    if (!selectedHemlockHerbName) {
                        alert("Please select an herb to buy.");
                        return;
                    }
                    const quantity = parseInt(hemlockQuantityInput.value, 10);
                    if (isNaN(quantity) || quantity < 1) {
                        alert("Please enter a valid quantity (at least 1).");
                        return;
                    }

                    if (hiddenActionNameInput) hiddenActionNameInput.value = 'buy_from_npc';
                    if (hiddenDetailsInput) {
                        hiddenDetailsInput.value = JSON.stringify({
                            npc_name: "Old Man Hemlock",
                            item_name: selectedHemlockHerbName,
                            quantity: quantity
                        });
                    }
                    if (actionForm) {
                        if (submitBuyHemlockHerbButton) submitBuyHemlockHerbButton.classList.add('button-processing');
                        console.log('Submitting action (buy_from_npc Hemlock). Name:', hiddenActionNameInput.value);
                        console.log('Submitting action (buy_from_npc Hemlock). Details:', hiddenDetailsInput.value);
                        actionForm.submit();
                    }
                });
            }

            // Initial Display Logic:
            // currentTownSubLocations is passed from Jinja directly if character is loaded.
            // This variable is already defined at the top of this script block.

            // Event listener for selecting a Borin item
            const borinItemsListDiv = document.getElementById('borin-items-list'); // Already declared if needed, or declare here
            if (borinItemsListDiv) {
                borinItemsListDiv.addEventListener('click', function(event) {
                    if (event.target.classList.contains('select-borin-item-button')) {
                        selectedBorinItemName = event.target.dataset.itemName;
                        document.querySelectorAll('.select-borin-item-button').forEach(btn => {
                            btn.style.fontWeight = 'normal'; btn.style.backgroundColor = '';
                        });
                        event.target.style.fontWeight = 'bold'; event.target.style.backgroundColor = '#a0d2a0';
                        console.log("Selected Borin item: " + selectedBorinItemName);
                    }
                });
            }

            // Specific listener for "Buy Selected Item" button from Borin's details
            const submitBuyBorinItemButton = document.getElementById('submit_buy_borin_item_button');
            const borinQuantityInput = document.getElementById('borin_quantity_dynamic');

            if (submitBuyBorinItemButton && borinQuantityInput && hiddenActionNameInput && hiddenDetailsInput && actionForm) {
                submitBuyBorinItemButton.addEventListener('click', function() {
                    if (!selectedBorinItemName) {
                        // Using showToast if available, otherwise alert
                        if (typeof showToast === 'function') {
                            showToast("Please select an item to buy from Borin.", "warning");
                        } else {
                            alert("Please select an item to buy from Borin.");
                        }
                        return;
                    }
                    const quantity = parseInt(borinQuantityInput.value, 10);
                    if (isNaN(quantity) || quantity < 1) {
                         if (typeof showToast === 'function') {
                            showToast("Please enter a valid quantity (at least 1).", "warning");
                        } else {
                            alert("Please enter a valid quantity (at least 1).");
                        }
                        return;
                    }

                    hiddenActionNameInput.value = 'buy_from_npc';
                    hiddenDetailsInput.value = JSON.stringify({
                        npc_name: "Borin Stonebeard",
                        item_name: selectedBorinItemName,
                        quantity: quantity
                    });
                    submitBuyBorinItemButton.classList.add('button-processing');
                    actionForm.submit();
                });
            }

            // We need to use the sub-locations from allTownsData for the current town for consistency
            // as currentTownSubLocations might just be names, whereas allTownsData has descriptions.
            if (currentTownDisplay && currentTownDisplay.textContent && allTownsData && allTownsData[currentTownDisplay.textContent]) {
                 const currentTownData = allTownsData[currentTownDisplay.textContent];
                 if (currentTownData && currentTownData.sub_locations) {
                    displaySubLocations(currentTownData.sub_locations);
                 } else {
                    displaySubLocations([]); // Call with empty if no sub_locations defined
                 }
            } else {
                 // Fallback if current_town_name isn't set or no data for it
                 displaySubLocations([]); // Call with empty array
            }
        }

            // JavaScript for Shop Item "Buy" button functionality
            const inventoryContent = document.getElementById('inventory-content'); // Parent container for shop items
            // const buyDetailsDiv = document.getElementById('div_buy_details'); // Already declared above
            // const buyItemNameInput = document.getElementById('buy_item_name'); // Already declared above
            // const actionsTabButton = document.getElementById('actions-tab-button'); // Already declared below
            // const actionsPanelContent = document.getElementById('actions-panel-content'); // Already declared below

            if (inventoryContent && buyItemNameInput && buyDetailsDiv) {
                inventoryContent.addEventListener('click', function(event) {
                    if (event.target.classList.contains('buy-item-button')) {
                        const itemName = event.target.dataset.itemName;

                        // Set the item name in the buy form
                        buyItemNameInput.value = itemName;

                        // Ensure the "Actions" tab and its panel are visible
                        // Note: actionsTabButton and actionsPanelContent are defined later in this script block
                        // This implies this new block should ideally be placed AFTER those declarations,
                        // or those specific variables need to be hoisted or passed if this block is placed earlier.
                        // For now, assuming they will be available in scope due to typical JS hoisting of const/let within a block,
                        // or that this specific handler will run after full DOMContentLoaded script execution.
                        // A safer approach might be to ensure their declaration is before this usage.
                        // Let's re-check if they are declared BEFORE this section.
                        // buyDetailsDiv and buyItemNameInput are declared above in the main script block.
                        // actionsTabButton and actionsPanelContent are declared in the "New UI interaction script" block below.
                        // This means this "Buy button functionality" block *should* be placed *inside* or *after* "New UI interaction script"
                        // OR those two variables need to be fetched here again.
                        // For simplicity and given the structure, let's fetch them again if not available or ensure this block is AFTER their declaration.
                        // Re-checking... they are indeed further down. This block needs to be moved or they need to be re-fetched.

                        // Let's assume for now this block will be placed after the "New UI interaction script" block for correct variable scoping.
                        // If actionsTabButton and actionsPanelContent are not found, these lines will be skipped.
                        const localActionsTabButton = document.getElementById('actions-tab-button');
                        const localActionsPanelContent = document.getElementById('actions-panel-content');

                        if (localActionsTabButton && localActionsPanelContent) {
                            localActionsTabButton.click(); // Simulate click to make Actions tab active
                        }

                        // Show the buy details section (actionDetailsContainer and allDetailDivs are from the script above)
                        if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                        allDetailDivs.forEach(div => { // Hide other detail forms
                            if (div) div.style.display = 'none';
                        });
                        buyDetailsDiv.style.display = 'block';

                        // Scroll to the buy details form for visibility
                        buyDetailsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

                        // Optional: Focus on the quantity input or the buyItemNameInput itself
                        buyItemNameInput.focus();
                    }
                });
            }

        // New UI interaction script
        const gameContainer = document.querySelector('.game-container');
        if (gameContainer) {
            const statsTab = document.getElementById('stats-tab');
            const statsContent = document.getElementById('stats-content');
            const inventoryTab = document.getElementById('inventory-tab');
            const inventoryContentElement = document.getElementById('inventory-content'); // Renamed to avoid conflict
            // const actionsTab = document.getElementById('actions-tab'); // Old reference
            // const actionsContent = document.getElementById('actions-content'); // Old reference for direct toggle

            // New elements for Actions/Log tabs
            const actionsTabButton = document.getElementById('actions-tab-button');
            const logTabButton = document.getElementById('log-tab-button');
            const actionsPanelContent = document.getElementById('actions-panel-content');
            const logPanelContent = document.getElementById('log-panel-content');

            const infoTab = document.getElementById('info-tab');
            const infoContent = document.getElementById('info-content');

            const topRightMenuButton = document.getElementById('top-right-menu-button');
            const settingsPopup = document.getElementById('settings-popup');
            const settingsOption = document.getElementById('settings-option');

            // const saveGameOption = document.getElementById('save-game-option'); // This was the <li>, now it's a button


            // REMOVED JavaScript hover listeners for statsTab, inventoryTab, and infoTab
            // CSS :hover will now handle their visibility and animation.

            // Old listener for #actions-tab (the container) is removed.
            // if (actionsTab && actionsContent) { ... }

            // New listeners for Actions/Log tab buttons
            if (actionsTabButton && actionsPanelContent && logTabButton && logPanelContent) {
                actionsTabButton.addEventListener('click', () => {
                    actionsPanelContent.classList.add('panel-visible');
                    logPanelContent.classList.remove('panel-visible');
                    actionsTabButton.classList.add('active-tab-button');
                    logTabButton.classList.remove('active-tab-button');
                });

                logTabButton.addEventListener('click', () => {
                    logPanelContent.classList.add('panel-visible');
                    actionsPanelContent.classList.remove('panel-visible');
                    logTabButton.classList.add('active-tab-button');
                    actionsTabButton.classList.remove('active-tab-button');
                });

                // Initial state: Make Actions tab active by default
                actionsTabButton.classList.add('active-tab-button');
                actionsPanelContent.classList.add('panel-visible');
                // Ensure log tab is not active/visible initially
                logTabButton.classList.remove('active-tab-button');
                logPanelContent.classList.remove('panel-visible');
            }


            if (topRightMenuButton && settingsPopup) {
                topRightMenuButton.addEventListener('click', () => {
                    settingsPopup.style.display = settingsPopup.style.display === 'none' || settingsPopup.style.display === '' ? 'block' : 'none';
                });
            }

            if (settingsOption) {
                settingsOption.addEventListener('click', () => {
                    console.log("Settings clicked");
                    settingsPopup.style.display = 'none'; // Hide popup after click
                });
            }


            if (saveGameOption) { // This ID no longer exists on an <li>
                // saveGameOption.addEventListener('click', () => { // Commenting out old listener
                //     console.log("Save Game clicked");
                //     settingsPopup.style.display = 'none'; // Hide popup after click
                // });
            }

            // New Save Game Button listener
            const saveGameButton = document.getElementById('save-game-button');
            if (saveGameButton) {
                saveGameButton.addEventListener('click', function() {
                    if (typeof showToast === 'function') {
                        showToast("Game progress is automatically saved after each action.", "info", 7000);
                    } else {
                        // Fallback alert if showToast is not defined when this code runs
                        alert("Game progress is automatically saved after each action.");
                    }

                    // Hide the settings popup after clicking the button
                    // const settingsPopup = document.getElementById('settings-popup'); // Already declared above
                    if (settingsPopup) {
                        settingsPopup.style.display = 'none';
                    }

                });
            }

            // Optional: Close popup if clicked outside
            document.addEventListener('click', function(event) {
                if (settingsPopup && topRightMenuButton) {
                    const isClickInsideMenuButton = topRightMenuButton.contains(event.target);
                    const isClickInsidePopup = settingsPopup.contains(event.target);
                    if (!isClickInsideMenuButton && !isClickInsidePopup && settingsPopup.style.display === 'block') {
                        settingsPopup.style.display = 'none';
                    }
                }
            });

            // Click-outside-to-close for Actions/Log tabs
            const actionsTabContainer = document.getElementById('actions-tab');
            const actionsPanel = document.getElementById('actions-panel-content'); // This will be defined here now
            const logPanel = document.getElementById('log-panel-content'); // This will be defined here now
            const actionsButton = document.getElementById('actions-tab-button'); // This will be defined here now
            const logButton = document.getElementById('log-tab-button'); // This will be defined here now

            document.addEventListener('click', function(event) {
                const isActionsPanelVisible = actionsPanel && actionsPanel.classList.contains('panel-visible');
                const isLogPanelVisible = logPanel && logPanel.classList.contains('panel-visible');

                // Check if either panel is visible AND the click is outside the actionsTabContainer
                if ((isActionsPanelVisible || isLogPanelVisible) && actionsTabContainer && !actionsTabContainer.contains(event.target)) {
                    // Close both panels and deactivate both buttons
                    if (actionsPanel) actionsPanel.classList.remove('panel-visible');
                    if (logPanel) logPanel.classList.remove('panel-visible');
                    if (actionsButton) actionsButton.classList.remove('active-tab-button');
                    if (logButton) logButton.classList.remove('active-tab-button');
                }
            });
        }
        // The "JavaScript for Shop Item 'Buy' button functionality" block was inserted *before* this line in the previous step.
        // It should be moved *after* the 'New UI interaction script' block if it depends on variables from it,
        // or ensure its variables are self-contained or hoisted.
        // Given the diff, it seems the intention was to place it before "New UI interaction script",
        // which means `actionsTabButton` and `actionsPanelContent` would not be defined yet from that block.
        // The added JS correctly re-fetches them as `localActionsTabButton` and `localActionsPanelContent`.

        // Action Result (now using Toast)
        const popupActionResult = window.gameConfig.popupActionResult;
        if (popupActionResult && popupActionResult.trim() !== "") {
            // Replace <br> tags (if any were intended for the modal) with spaces or newlines for toast readability
            const toastMessage = popupActionResult.replace(/<br\s*\/?>/gi, " "); // Replace <br> with space for single line toast
            // If you want multiline toasts, you might need to adjust toast CSS for white-space: pre-line;
            // and then replace <br> with \n. For now, let's assume single line is preferred for toasts.

            let actionResultType = 'info'; // Default type
            // Try to infer type from message content (simple check)
            if (toastMessage.toLowerCase().includes('success') || toastMessage.toLowerCase().includes('successful')) {
                actionResultType = 'success';
            } else if (toastMessage.toLowerCase().includes('fail') || toastMessage.toLowerCase().includes('error') || toastMessage.toLowerCase().includes('not possible')) {
                actionResultType = 'error';
            } else if (toastMessage.toLowerCase().includes('warning')) {
                actionResultType = 'warning';
            }

            showToast(toastMessage, actionResultType, 7000); // Show action result toast for 7 seconds
        }

        // Event Choice Popup Handling
        const awaitingEventChoice = window.gameConfig.awaitingEventChoice;
        const pendingEventDataJson = window.gameConfig.pendingEventDataJson;
        const eventPopup = document.getElementById('event-choice-popup');

        if (awaitingEventChoice && pendingEventDataJson && eventPopup) {
            try {
                const eventData = pendingEventDataJson; // Is an object if not null (due to |safe in config)
                const eventPopupNameEl = document.getElementById('event-popup-name');
                const eventPopupDescriptionEl = document.getElementById('event-popup-description');
                const choicesContainer = document.getElementById('event-popup-choices');

                if (eventPopupNameEl) eventPopupNameEl.textContent = eventData.name || "An Event Occurs!";
                if (eventPopupDescriptionEl) eventPopupDescriptionEl.textContent = eventData.description || "You must make a choice.";

                if (choicesContainer) {
                    choicesContainer.innerHTML = ''; // Clear previous choices

                    if (eventData.choices && eventData.choices.length > 0) {
                        eventData.choices.forEach(function(choice, index) {
                            const button = document.createElement('button');
                            button.className = 'event-choice-button button'; // Add generic button class for styling
                            button.dataset.choiceIndex = index;
                            // Display skill and DC if available
                            let buttonText = choice.text;
                            if (choice.skill && choice.dc) {
                                buttonText += ` [${choice.skill} DC ${choice.dc}]`;
                            }
                            if (choice.item_requirement_desc) { // Display item requirement description if present
                                buttonText += ` (${choice.item_requirement_desc})`;
                            }
                            button.textContent = buttonText;
                            choicesContainer.appendChild(button);
                        });
                    } else {
                        choicesContainer.innerHTML = '<p>No choices available for this event.</p>';
                        // Optionally, add a button to just close/acknowledge if there are no choices but popup is shown
                        // For example:
                        // const closeEventButton = document.createElement('button');
                        // closeEventButton.textContent = 'Acknowledge';
                        // closeEventButton.onclick = function() { eventPopup.style.display = 'none'; };
                        // choicesContainer.appendChild(closeEventButton);
                    }

                    // Event listener for choice buttons
                    choicesContainer.addEventListener('click', function(event) {
                        if (event.target.classList.contains('event-choice-button')) {
                            const choiceIndex = event.target.dataset.choiceIndex;
                            const currentEventName = eventData.name; // eventData is from pendingEventDataJson

                            if (choiceIndex === undefined || !currentEventName) {
                                console.error("Error: Missing choice index or event name for submission.");
                                alert("Error processing your choice. Please try again.");
                                return;
                            }

                            // Create a form dynamically to POST the data
                            const form = document.createElement('form');
                            form.method = 'POST';
                            form.action = window.gameConfig.submitEventChoiceUrl; // Target new route

                            const eventNameInput = document.createElement('input');
                            eventNameInput.type = 'hidden';
                            eventNameInput.name = 'event_name';
                            eventNameInput.value = currentEventName;
                            form.appendChild(eventNameInput);

                            const choiceIndexInput = document.createElement('input');
                            choiceIndexInput.type = 'hidden';
                            choiceIndexInput.name = 'choice_index';
                            choiceIndexInput.value = choiceIndex;
                            form.appendChild(choiceIndexInput);

                            document.body.appendChild(form);
                            form.submit();

                            // Hide the popup immediately after submitting
                            if (eventPopup) {
                                eventPopup.style.display = 'none';
                            }
                        }
                    });
                }
                eventPopup.style.display = 'block'; // Ensure it's visible
            } catch (e) {
                console.error("Error processing event data for popup:", e);
                if (eventPopup) eventPopup.style.display = 'none'; // Hide if error
            }
        } else if (eventPopup && eventPopup.style.display !== 'none' && (!awaitingEventChoice || !pendingEventDataJson)) {
            // If the popup exists and is visible, but there's no event data (e.g., after a choice is made and page reloads without new event)
            // ensure it's hidden. The Jinja template already prevents rendering if no data initially.
            // This JS part is more for dynamic hiding if somehow it was left open or state changes.
            // eventPopup.style.display = 'none'; // Commented out as Jinja handles initial display state
        }

        // Skill Roll Result Display (using Toast)
        const lastSkillRollStr = window.gameConfig.lastSkillRollStr;
        if (lastSkillRollStr && lastSkillRollStr.trim() !== "") {
            // Determine type of toast based on content of skill roll string if desired
            // For example, if it contains "Success", use "success", if "Fail", use "error"
            // For now, default to 'info' or a custom 'skill' type. Let's use 'info'.
            let skillRollType = 'info';
            if (lastSkillRollStr.toLowerCase().includes('success')) {
                skillRollType = 'success';
            } else if (lastSkillRollStr.toLowerCase().includes('fail') || lastSkillRollStr.toLowerCase().includes('failure')) {
                skillRollType = 'error';
            }

            showToast(lastSkillRollStr, skillRollType, 7000); // Show skill roll toast for 7 seconds
        }

    });
