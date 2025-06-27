// Main game interface script

// --- CONSTANTS ---
const CONSTANTS = {
    ACTION_NAMES: {
        ALLOCATE_SKILL_POINT: 'ALLOCATE_SKILL_POINT',
        PROCESS_ASI_FEAT_CHOICE: 'PROCESS_ASI_FEAT_CHOICE', // New action
        TRAVEL_TO_TOWN: 'travel_to_town',
        CRAFT: 'craft',
        BUY_FROM_OWN_SHOP: 'buy_from_own_shop',
        SELL_TO_OWN_SHOP: 'sell_to_own_shop',
        BUY_FROM_NPC: 'buy_from_npc',
        TALK_TO_BORIN: 'talk_to_borin', // Might be combined with BUY_FROM_NPC logic
        REPAIR_GEAR_BORIN: 'repair_gear_borin',
        GATHER_RESOURCES: 'gather_resources',
        STUDY_LOCAL_HISTORY: 'study_local_history',
        ORGANIZE_INVENTORY: 'organize_inventory',
        POST_ADVERTISEMENTS: 'post_advertisements',
        REST_SHORT: 'rest_short',
        REST_LONG: 'rest_long',
        SET_SHOP_SPECIALIZATION: 'set_shop_specialization',
        UPGRADE_SHOP: 'upgrade_shop',
    },
    NPC_NAMES: {
        HEMLOCK: "Old Man Hemlock",
        BORIN: "Borin Stonebeard",
    },
    SUB_LOCATIONS: {
        HEMLOCK_HUT: "Old Man Hemlock's Hut",
        BORIN_SMITHY: "Borin Stonebeard's Smithy",
    }
};

const UIAsiFeatChoice = {
    selectedMainChoice: null, // 'asi' or 'feat'
    selectedAsiType: null, // 'plus_two' or 'plus_one_one'
    selectedFeatId: null,

    updateVisibility() {
        DOM.asiOptionsContainer.classList.toggle('hidden', this.selectedMainChoice !== 'asi');
        DOM.featOptionsContainer.classList.toggle('hidden', this.selectedMainChoice !== 'feat');

        if (this.selectedMainChoice === 'asi') {
            DOM.asiPlusTwoOptionsDiv.classList.toggle('hidden', this.selectedAsiType !== 'plus_two');
            DOM.asiPlusOneOneOptionsDiv.classList.toggle('hidden', this.selectedAsiType !== 'plus_one_one');
        }
        this.validateAndToggleButton();
    },

    populateFeatList() {
        if (!DOM.featSelectionListDiv) return;
        DOM.featSelectionListDiv.innerHTML = ''; // Clear previous
        const feats = gameConfigData.featDefinitionsJson;

        if (!feats || feats.length === 0) {
            DOM.featSelectionListDiv.innerHTML = '<p>No feats available at this time.</p>';
            return;
        }

        feats.forEach(feat => {
            const label = document.createElement('label');
            label.className = 'feat-choice-label';
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'feat_choice_radio';
            input.value = feat.id;
            input.addEventListener('change', () => {
                this.selectedFeatId = input.value;
                this.validateAndToggleButton();
            });

            label.appendChild(input);
            label.appendChild(document.createTextNode(` ${feat.name}`));
            const desc = document.createElement('p');
            desc.className = 'feat-description';
            desc.textContent = feat.description;
            label.appendChild(desc);
            DOM.featSelectionListDiv.appendChild(label);
        });
    },

    validateAndToggleButton() {
        let isValid = false;
        if (this.selectedMainChoice === 'asi') {
            if (this.selectedAsiType === 'plus_two') {
                isValid = !!DOM.asiPlusTwoStatSelect.value;
            } else if (this.selectedAsiType === 'plus_one_one') {
                const stat1 = DOM.asiPlusOneStat1Select.value;
                const stat2 = DOM.asiPlusOneStat2Select.value;
                isValid = stat1 && stat2 && stat1 !== stat2;
            }
        } else if (this.selectedMainChoice === 'feat') {
            isValid = !!this.selectedFeatId;
        }
        DOM.confirmAsiFeatChoiceButton.disabled = !isValid;
    },

    resetSelections() {
        // No event active check here, this is a helper for resetting state.
        this.selectedMainChoice = null;
        this.selectedAsiType = null;
        this.selectedFeatId = null;

        if(DOM.asiFeatMainChoiceAsiRadio) DOM.asiFeatMainChoiceAsiRadio.checked = false;
        if(DOM.asiFeatMainChoiceFeatRadio) DOM.asiFeatMainChoiceFeatRadio.checked = false;
        if(DOM.asiIncreaseTypePlusTwoRadio) DOM.asiIncreaseTypePlusTwoRadio.checked = false;
        if(DOM.asiIncreaseTypePlusOneOneRadio) DOM.asiIncreaseTypePlusOneOneRadio.checked = false;

        if(DOM.asiPlusTwoStatSelect) DOM.asiPlusTwoStatSelect.value = '';
        if(DOM.asiPlusOneStat1Select) DOM.asiPlusOneStat1Select.value = '';
        if(DOM.asiPlusOneStat2Select) DOM.asiPlusOneStat2Select.value = '';

        const featRadios = DOM.featSelectionListDiv.querySelectorAll('input[name="feat_choice_radio"]');
        featRadios.forEach(radio => radio.checked = false);

        this.updateVisibility();
    },

    openModal() {
        if (isEventActive() && DOM.asiFeatChoicePopupWrapper && DOM.asiFeatChoicePopupWrapper.classList.contains('hidden')) {
            // If an event is active AND this ASI/Feat popup is currently hidden (i.e., we're trying to show it)
            // then prevent showing it.
            showToast("Cannot make ASI/Feat choice while a game event is active.", "warning");
            return;
        }
        if (DOM.asiFeatChoicePopupWrapper) {
            this.resetSelections();
            this.populateFeatList();
            DOM.asiFeatChoicePopupWrapper.classList.remove('hidden');
            DOM.asiFeatChoicePopup.setAttribute('aria-hidden', 'false');
            // Focus management can be added here if needed
        }
    },

    closeModal() { // Though not used if choice is mandatory
        if (DOM.asiFeatChoicePopupWrapper) {
            DOM.asiFeatChoicePopupWrapper.classList.add('hidden');
            DOM.asiFeatChoicePopup.setAttribute('aria-hidden', 'true');
        }
    },

    handleSubmit() {
        if (isEventActive()) {
            // ASI/Feat choice is modal itself. If an event is active, this modal shouldn't even be reachable.
            // This is a defensive check.
            showToast("Please resolve the current game event before making ASI/Feat choices.", "warning");
            return;
        }
        let actionDetails = {};
        if (this.selectedMainChoice === 'asi') {
            actionDetails.choice_type = 'asi';
            if (this.selectedAsiType === 'plus_two') {
                actionDetails.stat_primary = DOM.asiPlusTwoStatSelect.value;
                actionDetails.points_primary = 2;
            } else if (this.selectedAsiType === 'plus_one_one') {
                actionDetails.stat_primary = DOM.asiPlusOneStat1Select.value;
                actionDetails.points_primary = 1;
                actionDetails.stat_secondary = DOM.asiPlusOneStat2Select.value;
                actionDetails.points_secondary = 1;
            }
        } else if (this.selectedMainChoice === 'feat') {
            actionDetails.choice_type = 'feat';
            actionDetails.feat_id = this.selectedFeatId;
        }

        if (DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.PROCESS_ASI_FEAT_CHOICE;
            DOM.hiddenDetailsInput.value = JSON.stringify(actionDetails);
            DOM.actionForm.submit();
            this.closeModal(); // Close after submission
        } else {
            console.error("Form elements missing for ASI/Feat choice submission.");
            showToast("Error submitting your choice.", "error");
        }
    },

    init() {
        if (!DOM.asiFeatChoicePopupWrapper || !gameConfigData.playerPendingAsiFeatChoice) {
            if (DOM.asiFeatChoicePopupWrapper) DOM.asiFeatChoicePopupWrapper.classList.add('hidden'); // Ensure hidden if not pending
            return;
        }
        this.openModal(); // Open if pending

        // Main choice (ASI vs Feat)
        [DOM.asiFeatMainChoiceAsiRadio, DOM.asiFeatMainChoiceFeatRadio].forEach(radio => {
            if(radio) radio.addEventListener('change', (event) => {
                this.selectedMainChoice = event.target.value;
                this.selectedAsiType = null; // Reset sub-choice
                this.selectedFeatId = null;  // Reset sub-choice
                if(DOM.asiIncreaseTypePlusTwoRadio) DOM.asiIncreaseTypePlusTwoRadio.checked = false;
                if(DOM.asiIncreaseTypePlusOneOneRadio) DOM.asiIncreaseTypePlusOneOneRadio.checked = false;
                const featRadios = DOM.featSelectionListDiv.querySelectorAll('input[name="feat_choice_radio"]');
                featRadios.forEach(r => r.checked = false);
                this.updateVisibility();
            });
        });

        // ASI type choice (+2 vs +1/+1)
        [DOM.asiIncreaseTypePlusTwoRadio, DOM.asiIncreaseTypePlusOneOneRadio].forEach(radio => {
           if(radio) radio.addEventListener('change', (event) => {
                this.selectedAsiType = event.target.value;
                this.updateVisibility();
            });
        });

        // Stat selection dropdowns for ASI
        [DOM.asiPlusTwoStatSelect, DOM.asiPlusOneStat1Select, DOM.asiPlusOneStat2Select].forEach(select => {
            if(select) select.addEventListener('change', () => this.validateAndToggleButton());
        });

        // Confirm button
        if(DOM.confirmAsiFeatChoiceButton) DOM.confirmAsiFeatChoiceButton.addEventListener('click', () => this.handleSubmit());

        // Initial validation check
        this.updateVisibility();
    }
};

// --- GLOBAL STATE (scoped within this IIFE if script becomes a module) ---
let currentOpenDynamicForm = null;
let currentSubLocationName = null;
let selectedHemlockHerbName = null;
let selectedBorinItemName = null;

// --- DOM ELEMENT REFERENCES (grouped by functionality) ---
// Populated in `cacheDomElements`
const DOM = {};

function cacheDomElements() {
    // Main Action Form
    DOM.actionForm = document.getElementById('actionForm');
    DOM.hiddenActionNameInput = document.getElementById('action_name_hidden');
    DOM.hiddenDetailsInput = document.getElementById('action_details');

    // Side Info Columns & Panels
    DOM.miniPanels = document.querySelectorAll('.mini-panel');
    DOM.fullPanelContainers = document.querySelectorAll('.full-panel-container');
    DOM.closeFullPanelButtons = document.querySelectorAll('.close-full-panel');

    // Map & Travel
    DOM.mapDestinationsDiv = document.getElementById('map-destinations');

    // Location Interactions (Bottom Bar - Actions Panel)
    DOM.subLocationsListDiv = document.getElementById('sub-locations-list');
    DOM.currentSubLocationNameDisplay = document.getElementById('current-sub-location-name-display');
    DOM.currentSubLocationActionsListDiv = document.getElementById('current-sub-location-actions-list');
    DOM.currentTownDisplayActions = document.getElementById('current-town-display-actions');

    // Dynamic Action Forms Area (Bottom Bar - Actions Panel)
    DOM.dynamicActionFormsContainer = document.getElementById('dynamic-action-forms-container');
    DOM.allDynamicForms = DOM.dynamicActionFormsContainer ? DOM.dynamicActionFormsContainer.querySelectorAll('.dynamic-form') : [];
    DOM.closeDynamicFormButtons = DOM.dynamicActionFormsContainer ? DOM.dynamicActionFormsContainer.querySelectorAll('.close-dynamic-form') : [];
    DOM.travelActionsContainer = document.getElementById('travel-actions-container');
    DOM.locationInteractionsContainer = document.getElementById('location-interactions-container');
    DOM.generalActionsContainer = document.getElementById('general-actions-container');


    // Specific Detail Form Elements
    DOM.craftDetailsDiv = document.getElementById('div_craft_details');
    DOM.craftItemNameInput = document.getElementById('craft_item_name');

    DOM.buyDetailsDiv = document.getElementById('div_buy_details');
    DOM.buyItemNameInput = document.getElementById('buy_item_name');
    DOM.buyQuantityInput = document.getElementById('buy_quantity');

    DOM.sellDetailsDiv = document.getElementById('div_sell_details');
    DOM.sellItemNameInput = document.getElementById('sell_item_name');
    DOM.sellItemDropdown = document.getElementById('sell_item_dropdown');

    // Hemlock (NPC)
    DOM.hemlockHerbsDetailsDiv = document.getElementById('div_hemlock_herbs_details');
    DOM.hemlockHerbsListDiv = document.getElementById('hemlock-herbs-list');
    DOM.hemlockQuantityInput = document.getElementById('hemlock_quantity_dynamic');
    // DOM.submitBuyHemlockHerbButton = document.getElementById('submit_buy_hemlock_herb_button'); // Covered by delegation

    // Borin (NPC)
    DOM.borinItemsDetailsDiv = document.getElementById('div_borin_items_details');
    DOM.borinItemsListDiv = document.getElementById('borin-items-list');
    DOM.borinQuantityInput = document.getElementById('borin_quantity_dynamic');
    // DOM.submitBuyBorinItemButton = document.getElementById('submit_buy_borin_item_button'); // Covered by delegation
    DOM.borinRepairDetailsDiv = document.getElementById('div_borin_repair_details');
    DOM.borinRepairItemSelect = document.getElementById('borin-repair-item-select');
    DOM.borinRepairCostDisplay = document.getElementById('borin-repair-cost-display');
    // DOM.submitBorinRepairButton = document.getElementById('submit-borin-repair-button'); // Covered by delegation

    // Shop Management
    DOM.shopManagementDetailsDiv = document.getElementById('shop-management-details');
    DOM.fullShopMgtPanelContainer = document.getElementById('full-shop-mgt-panel-container'); // Assuming this is the outer container
    DOM.miniShopMgtPanel = document.getElementById('mini-shop-mgt-panel'); // Assuming this is the trigger

    // Inventory
    DOM.fullInventoryPanel = document.getElementById('full-inventory-panel'); // Content area
    DOM.fullInventoryPanelContainer = document.getElementById('full-inventory-panel-container');
    DOM.miniInventoryPanel = document.getElementById('mini-inventory-panel');


    // Bottom Bar Tabs
    DOM.actionsTabButton = document.getElementById('actions-tab-button');
    DOM.logTabButton = document.getElementById('log-tab-button');
    DOM.actionsPanelContent = document.getElementById('actions-panel-content');
    DOM.logPanelContent = document.getElementById('log-panel-content');

    // Top Right Menu
    DOM.topRightMenuButton = document.getElementById('top-right-menu-button');
    DOM.settingsPopup = document.getElementById('settings-popup');
    // DOM.settingsOption = document.getElementById('settings-option'); // Potentially unused
    DOM.saveGameButton = document.getElementById('save-game-button');

    // General Action Buttons
    DOM.gatherResourcesButton = document.getElementById('gatherResourcesButton');
    DOM.studyLocalHistoryButton = document.getElementById('studyLocalHistoryButton');
    DOM.organizeInventoryButton = document.getElementById('organizeInventoryButton');
    DOM.postAdvertisementsButton = document.getElementById('postAdvertisementsButton');
    DOM.shortRestButton = document.getElementById('shortRestButton');
    DOM.longRestButton = document.getElementById('longRestButton');

    // Event Popup
    DOM.eventPopup = document.getElementById('event-choice-popup');
    DOM.eventPopupNameEl = document.getElementById('event-popup-name');
    DOM.eventPopupDescriptionEl = document.getElementById('event-popup-description');
    DOM.eventPopupChoicesContainer = document.getElementById('event-popup-choices');

    // Skill Allocation Popup
    DOM.allocateSkillPointsButton = document.getElementById('allocate-skill-points-button');
    DOM.skillAllocationPopupWrapper = document.getElementById('skill-allocation-popup-wrapper');
    DOM.skillAllocationPopup = document.getElementById('skill-allocation-popup');
    DOM.skillAllocationChoicesContainer = document.getElementById('skill-allocation-choices');
    DOM.skillPointsAvailableModalDisplay = document.getElementById('skill-points-available-modal-display');
    DOM.closeSkillAllocationPopupButton = document.getElementById('close-skill-allocation-popup');

    // ASI/Feat Choice Popup
    DOM.asiFeatChoicePopupWrapper = document.getElementById('asi-feat-choice-popup-wrapper');
    DOM.asiFeatChoicePopup = document.getElementById('asi-feat-choice-popup');
    DOM.asiFeatMainChoiceAsiRadio = document.querySelector('input[name="asi_feat_type_choice"][value="asi"]');
    DOM.asiFeatMainChoiceFeatRadio = document.querySelector('input[name="asi_feat_type_choice"][value="feat"]');
    DOM.asiOptionsContainer = document.getElementById('asi-options-container');
    DOM.asiIncreaseTypePlusTwoRadio = document.querySelector('input[name="asi_increase_type"][value="plus_two"]');
    DOM.asiIncreaseTypePlusOneOneRadio = document.querySelector('input[name="asi_increase_type"][value="plus_one_one"]');
    DOM.asiPlusTwoOptionsDiv = document.getElementById('asi-plus-two-options');
    DOM.asiPlusTwoStatSelect = document.getElementById('asi_plus_two_stat');
    DOM.asiPlusOneOneOptionsDiv = document.getElementById('asi-plus-one-one-options');
    DOM.asiPlusOneStat1Select = document.getElementById('asi_plus_one_stat1');
    DOM.asiPlusOneStat2Select = document.getElementById('asi_plus_one_stat2');
    DOM.featOptionsContainer = document.getElementById('feat-options-container');
    DOM.featSelectionListDiv = document.getElementById('feat-selection-list');
    DOM.confirmAsiFeatChoiceButton = document.getElementById('confirm-asi-feat-choice-button');

    // Haggling Modal Elements
    DOM.hagglingPopupWrapper = document.getElementById('haggling-popup-wrapper');
    DOM.hagglingPopup = document.getElementById('haggling-popup');
    DOM.hagglingPopupTitle = document.getElementById('haggling-popup-title');
    DOM.haggleItemName = document.getElementById('haggle-item-name');
    DOM.haggleItemQuality = document.getElementById('haggle-item-quality');
    DOM.haggleItemQuantity = document.getElementById('haggle-item-quantity');
    DOM.haggleNpcName = document.getElementById('haggle-npc-name');
    DOM.haggleNpcMood = document.getElementById('haggle-npc-mood');
    DOM.haggleCurrentOffer = document.getElementById('haggle-current-offer');
    DOM.haggleTargetPriceInfo = document.getElementById('haggle-target-price-info'); // Optional display
    DOM.hagglePlayerTargetPrice = document.getElementById('haggle-player-target-price');
    DOM.haggleShopTargetPrice = document.getElementById('haggle-shop-target-price');
    DOM.haggleLastCheckResult = document.getElementById('haggle-last-check-result');
    DOM.haggleLastCheckText = document.getElementById('haggle-last-check-text');
    DOM.hagglingChoicesContainer = document.getElementById('haggling-choices-container');
    DOM.haggleAcceptButton = document.getElementById('haggle-accept-button');
    DOM.haggleDeclineButton = document.getElementById('haggle-decline-button');
    DOM.hagglePersuadeButton = document.getElementById('haggle-persuade-button');
    DOM.haggleRoundsInfo = document.getElementById('haggle-rounds-info');
    DOM.haggleCurrentRound = document.getElementById('haggle-current-round');
    DOM.haggleMaxRounds = document.getElementById('haggle-max-rounds');
    DOM.haggleFinalOfferNotice = document.getElementById('haggle-final-offer-notice');
    console.log('[cacheDomElements] DOM.hagglingChoicesContainer:', DOM.hagglingChoicesContainer); // Added log


    // Toast Container
    DOM.toastContainer = document.getElementById('toast-container');
}

// --- GLOBAL HELPER FOR EVENT STATE ---
function isEventActive() {
    // Check if the event-active class is on the body (primary check)
    if (document.body.classList.contains('event-active')) {
        return true;
    }
    // Fallback: Check if the event popup DOM element is visible.
    // DOM.eventPopup might not be cached yet if this is called very early.
    const eventPopupElement = document.getElementById('event-choice-popup');
    if (eventPopupElement && eventPopupElement.style.display === 'block') {
        // To be absolutely sure, also check the wrapper if it exists, as per HTML structure
        const eventPopupWrapper = document.getElementById('event-choice-popup-wrapper');
        if (eventPopupWrapper && !eventPopupWrapper.classList.contains('hidden')) {
            return true;
        }
        // If only eventPopup is checked, it might be a false positive if wrapper is hidden
        // However, processEventPopup controls eventPopup.style.display directly.
    }
    return false;
}


// --- CONFIG DATA (scoped) ---
let gameConfigData = {};
function loadConfigData() {
    gameConfigData.allTownsData = window.gameConfig.allTownsDataJson || {};
    gameConfigData.hemlockHerbsData = window.gameConfig.hemlockHerbsData || {};
    gameConfigData.borinItemsData = window.gameConfig.borinItemsData || {};
    gameConfigData.shopData = window.gameConfig.shopData;
    gameConfigData.shopConfig = window.gameConfig.shopConfig;
    gameConfigData.playerInventoryForSellDropdown = window.gameConfig.playerInventory || [];
    gameConfigData.playerGold = window.gameConfig.playerGold;
    gameConfigData.popupActionResult = window.gameConfig.popupActionResult;
    gameConfigData.awaitingEventChoice = window.gameConfig.awaitingEventChoice;
    gameConfigData.pendingEventDataJson = window.gameConfig.pendingEventDataJson;
    gameConfigData.lastSkillRollStr = window.gameConfig.lastSkillRollStr;
    gameConfigData.submitEventChoiceUrl = window.gameConfig.submitEventChoiceUrl;
    // New config data for skill allocation
    gameConfigData.playerSkillPointsToAllocate = window.gameConfig.playerSkillPointsToAllocate || 0;
    gameConfigData.playerChosenSkillBonuses = window.gameConfig.playerChosenSkillBonuses || {};
    gameConfigData.characterAttributeDefinitions = window.gameConfig.characterAttributeDefinitions || {};
    // ASI/Feat Choice config
    gameConfigData.playerPendingAsiFeatChoice = window.gameConfig.playerPendingAsiFeatChoice || false;
    gameConfigData.featDefinitionsJson = window.gameConfig.featDefinitionsJson || [];
    gameConfigData.playerStatsJson = window.gameConfig.playerStatsJson || {};
    // Haggling config
    gameConfigData.hagglingPending = window.gameConfig.hagglingPending || false;
    gameConfigData.pendingHagglingDataJson = window.gameConfig.pendingHagglingDataJson || null;
}


// --- HELPER FUNCTIONS ---
function showToast(message, type = 'info', duration = 5000) {
    if (!DOM.toastContainer) {
        console.error('Toast container not found!');
        return;
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    let iconHtml = '';
    if (type === 'success') iconHtml = '<span class="toast-icon">✔️</span>';
    else if (type === 'error') iconHtml = '<span class="toast-icon">❌</span>';
    else if (type === 'warning') iconHtml = '<span class="toast-icon">⚠️</span>';
    else iconHtml = '<span class="toast-icon">ℹ️</span>';
    toast.innerHTML = `${iconHtml} <span class="toast-message">${message}</span>`;
    DOM.toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 100); // Delay for CSS transition
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.parentElement?.removeChild(toast));
    }, duration);
}
// Make showToast globally accessible if needed by other scripts or inline event handlers (though ideally not)
window.showToast = showToast;


function hideAllDynamicForms() {
    if (DOM.dynamicActionFormsContainer) DOM.dynamicActionFormsContainer.classList.add('hidden'); // Add hidden class
    if (DOM.allDynamicForms) DOM.allDynamicForms.forEach(form => form.classList.add('hidden')); // Add hidden class for all individual dynamic forms
    currentOpenDynamicForm = null;

    // Make other action sections visible again by removing 'hidden' class
    // Assuming these containers might also use the .hidden class convention
    if (DOM.travelActionsContainer) DOM.travelActionsContainer.classList.remove('hidden');
    if (DOM.locationInteractionsContainer) DOM.locationInteractionsContainer.classList.remove('hidden');
    if (DOM.generalActionsContainer) DOM.generalActionsContainer.classList.remove('hidden');
}

function showDynamicForm(formElement) {
    hideAllDynamicForms(); // Hide any currently open form and show main action sections
    if (formElement) {
        // Hide other action sections to focus on the form, by adding 'hidden' class
        if (DOM.travelActionsContainer) DOM.travelActionsContainer.classList.add('hidden');
        if (DOM.locationInteractionsContainer) DOM.locationInteractionsContainer.classList.add('hidden');
        if (DOM.generalActionsContainer) DOM.generalActionsContainer.classList.add('hidden');

        // Show the main dynamic forms container and the specific form by removing 'hidden' class
        if (DOM.dynamicActionFormsContainer) DOM.dynamicActionFormsContainer.classList.remove('hidden');
        formElement.classList.remove('hidden'); // This is the specific form like DOM.craftDetailsDiv

        currentOpenDynamicForm = formElement;
        // Scroll into view after it's made visible
        requestAnimationFrame(() => { // Ensure DOM update before scrolling
            formElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    } else {
        // If no formElement is provided, hideAllDynamicForms has already run,
        // so the main action sections should be visible.
    }
}



// --- INITIALIZATION MODULES ---

const UIPanels = {
    init() {
        if (!DOM.miniPanels || !DOM.closeFullPanelButtons || !DOM.fullPanelContainers) return;


        DOM.miniPanels.forEach(miniPanel => {
            const fullPanelId = miniPanel.getAttribute('aria-controls');
            const fullPanelContainer = document.getElementById(fullPanelId);

            if (fullPanelContainer) {
                const openPanel = () => {
                    // Hide all other full panels first
                    DOM.fullPanelContainers.forEach(p => {
                        if (p !== fullPanelContainer) {
                            p.classList.add('hidden');
                            const correspondingMiniPanel = document.querySelector(`[aria-controls="${p.id}"]`);
                            if (correspondingMiniPanel) {
                                correspondingMiniPanel.setAttribute('aria-expanded', 'false');
                            }
                        }
                    });
                    fullPanelContainer.classList.remove('hidden');
                    miniPanel.setAttribute('aria-expanded', 'true');
                };
                miniPanel.addEventListener('click', openPanel);
                miniPanel.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        openPanel();
                    }
                });
            }
        });

        DOM.closeFullPanelButtons.forEach(button => {
            button.addEventListener('click', () => {
                const fullPanelContainer = button.closest('.full-panel-container');
                if (fullPanelContainer) {
                    fullPanelContainer.classList.add('hidden');
                    const miniPanel = document.querySelector(`[aria-controls="${fullPanelContainer.id}"]`);
                    if (miniPanel) miniPanel.setAttribute('aria-expanded', 'false');
                }
            });
        });

        DOM.fullPanelContainers.forEach(container => {
            container.addEventListener('click', function(event) {
                if (event.target === container) { // Click on overlay, not content
                    container.classList.add('hidden');
                    const miniPanel = document.querySelector(`[aria-controls="${container.id}"]`);
                    if (miniPanel) miniPanel.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }
};

const UIBottomTabs = {
    init() {
        if (!DOM.actionsTabButton || !DOM.logTabButton || !DOM.actionsPanelContent || !DOM.logPanelContent) return;

        const switchTab = (activeTab, inactiveTab, activePanel, inactivePanel) => {
            // Rely on CSS classes for visibility: .panel-content is display:none, .panel-visible is display:block
            activePanel.classList.add('panel-visible');
            activePanel.classList.remove('hidden'); // Ensure 'hidden' class is removed
            inactivePanel.classList.remove('panel-visible');
            // inactivePanel.classList.add('hidden'); // Optionally add back if other logic relies on it, but CSS default should be enough

            activeTab.classList.add('active-tab-button');
            inactiveTab.classList.remove('active-tab-button');
            activeTab.setAttribute('aria-selected', 'true');
            inactiveTab.setAttribute('aria-selected', 'false');
        };

        DOM.actionsTabButton.addEventListener('click', () => {
            switchTab(DOM.actionsTabButton, DOM.logTabButton, DOM.actionsPanelContent, DOM.logPanelContent);
        });

        DOM.logTabButton.addEventListener('click', () => {
            switchTab(DOM.logTabButton, DOM.actionsTabButton, DOM.logPanelContent, DOM.actionsPanelContent);
        });

        // Initial state: Actions tab is active
        DOM.actionsTabButton.click();
    }
};

const UIShopAndInventory = {
    populateSellDropdown() {
        if (!DOM.sellItemDropdown || !gameConfigData.playerInventoryForSellDropdown) return;
        DOM.sellItemDropdown.innerHTML = '<option value="">-- Select an item to sell --</option>';
        gameConfigData.playerInventoryForSellDropdown.forEach(item => {
            const option = document.createElement('option');
            const itemName = (typeof item === 'string') ? item : (item && item.name);
            if (!itemName) return;
            option.value = itemName;
            option.textContent = itemName; // Consider adding quantity if available: e.g., `${itemName} (x${item.quantity})`
            DOM.sellItemDropdown.appendChild(option);
        });
    },

    initSellFunctionality() {
        if (DOM.sellItemDropdown && DOM.sellItemNameInput) {
            DOM.sellItemDropdown.addEventListener('change', function() {
                if (this.value && DOM.sellItemNameInput) {
                    DOM.sellItemNameInput.value = this.value;
                }
            });
        }
        if (DOM.sellItemDropdown) this.populateSellDropdown();
    },

    initShopBuyButtonFunctionality() {
        if (DOM.fullInventoryPanel && DOM.buyItemNameInput && DOM.buyDetailsDiv) {
            DOM.fullInventoryPanel.addEventListener('click', (event) => {
                if (event.target.classList.contains('buy-item-button')) {
                    const itemName = event.target.dataset.itemName;
                    if (DOM.buyItemNameInput) DOM.buyItemNameInput.value = itemName;

                    if (DOM.fullInventoryPanelContainer) DOM.fullInventoryPanelContainer.style.display = 'none';
                    if (DOM.miniInventoryPanel) DOM.miniInventoryPanel.setAttribute('aria-expanded', 'false');

                    if (DOM.actionsTabButton) DOM.actionsTabButton.click();
                    showDynamicForm(DOM.buyDetailsDiv);
                    if (DOM.buyItemNameInput) DOM.buyItemNameInput.focus();
                }
            });
        }
    },

    populateShopManagementUI() {
        if (!DOM.shopManagementDetailsDiv || !gameConfigData.shopData || !gameConfigData.shopConfig) {
            if (DOM.shopManagementDetailsDiv) DOM.shopManagementDetailsDiv.innerHTML = '<p>Shop data not available.</p>';
            return;
        }
        const { shopData, shopConfig, playerGold } = gameConfigData;
        let html = `<h3>${shopData.name}</h3>`;
        html += `<p>Level: ${shopData.level} (Quality Bonus: +${shopData.current_quality_bonus})</p>`;
        html += `<p>Specialization: ${shopData.specialization}</p>`;
        html += `<p>Inventory: ${shopData.inventory_count} / ${shopData.max_inventory_slots} slots</p>`;
        html += `<p>Player Gold: ${playerGold !== undefined ? playerGold : 'N/A'}</p>`;

        html += `<h4>Change Specialization</h4><select id="shop-specialization-select" class="themed-select">`;
        shopConfig.specialization_types.forEach(specType => {
            html += `<option value="${specType}" ${shopData.specialization === specType ? 'selected' : ''}>${specType.replace(/_/g, ' ')}</option>`;
        });
        html += `</select><button type="button" id="submit-change-specialization" class="action-button">Set Specialization</button>`;

        html += `<h4>Upgrade Shop</h4>`;
        if (shopData.max_level_reached) {
            html += `<p>Shop is at maximum level (${shopConfig.max_shop_level}).</p>`;
        } else {
            html += `<p>Next Level: ${shopData.level + 1}</p><p>Cost: ${shopData.next_level_cost} Gold</p>`;
            html += `<p>Max Inventory Slots: ${shopData.next_level_slots}</p><p>Crafting Quality Bonus: +${shopData.next_level_quality_bonus}</p>`;
            html += `<button type="button" id="submit-upgrade-shop" class="action-button">Upgrade Shop</button>`;
        }
        DOM.shopManagementDetailsDiv.innerHTML = html;

        // Re-attach event listeners after innerHTML overwrite
        this.attachShopManagementActionListeners();
    },

    attachShopManagementActionListeners() {
        const changeSpecButton = document.getElementById('submit-change-specialization');
        if (changeSpecButton && DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            changeSpecButton.addEventListener('click', () => {
                if (isEventActive()) {
                    showToast("Please resolve the current event first.", "warning");
                    return;
                }
                const selectElement = document.getElementById('shop-specialization-select');
                DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.SET_SHOP_SPECIALIZATION;
                DOM.hiddenDetailsInput.value = JSON.stringify({ specialization_name: selectElement.value });
                DOM.actionForm.submit();
            });
        }
        const upgradeShopButton = document.getElementById('submit-upgrade-shop');
        if (upgradeShopButton && DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            upgradeShopButton.addEventListener('click', () => {
                if (isEventActive()) {
                    showToast("Please resolve the current event first.", "warning");
                    return;
                }
                DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.UPGRADE_SHOP;
                DOM.hiddenDetailsInput.value = JSON.stringify({});
                DOM.actionForm.submit();
            });
        }
    },

    initShopManagementInterface() {
        if (DOM.shopManagementDetailsDiv && gameConfigData.shopData) {
            this.populateShopManagementUI();
            // If the panel is opened dynamically, populateShopManagementUI should be called then.
            // For now, assuming it might be visible on load or its content is prepped.
        }
    },

    init() {
        this.initSellFunctionality();
        this.initShopBuyButtonFunctionality();
        this.initShopManagementInterface();
    }
};


const UIActionsAndEvents = {
    displaySubLocations() {
        if (!DOM.subLocationsListDiv || !DOM.currentTownDisplayActions) return;
        DOM.subLocationsListDiv.innerHTML = '';
        if (DOM.currentSubLocationActionsListDiv) DOM.currentSubLocationActionsListDiv.innerHTML = '';
        if (DOM.currentSubLocationNameDisplay) DOM.currentSubLocationNameDisplay.style.display = 'none';
        hideAllDynamicForms();

        const currentTownName = DOM.currentTownDisplayActions.textContent;
        const townData = gameConfigData.allTownsData[currentTownName];

        if (townData && townData.sub_locations && townData.sub_locations.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'button-list';
            townData.sub_locations.forEach(subLoc => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'action-button sub-location-button';
                button.dataset.sublocName = subLoc.name;
                button.textContent = subLoc.name;
                li.appendChild(button);
                ul.appendChild(li);
            });
            DOM.subLocationsListDiv.appendChild(ul);
        } else {
            DOM.subLocationsListDiv.innerHTML = '<p>No sub-locations here.</p>';
        }
    },

    displaySubLocationActions(subLocName) {
        if (!DOM.currentSubLocationActionsListDiv || !DOM.currentSubLocationNameDisplay) return;
        DOM.currentSubLocationActionsListDiv.innerHTML = '';
        hideAllDynamicForms();

        currentSubLocationName = subLocName; // Update global state
        DOM.currentSubLocationNameDisplay.textContent = subLocName;
        DOM.currentSubLocationNameDisplay.style.display = 'block';

        const currentTownName = DOM.currentTownDisplayActions.textContent;
        const townData = gameConfigData.allTownsData[currentTownName];
        const selectedSubLocation = townData?.sub_locations?.find(sl => sl.name === subLocName);

        if (selectedSubLocation && selectedSubLocation.actions && selectedSubLocation.actions.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'button-list';
            selectedSubLocation.actions.forEach(actionStr => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'action-button subloc-action-button';
                button.dataset.actionName = actionStr;
                button.textContent = actionStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                li.appendChild(button);
                ul.appendChild(li);
            });
            DOM.currentSubLocationActionsListDiv.appendChild(ul);
        } else {
            DOM.currentSubLocationActionsListDiv.innerHTML = '<p>No actions available here.</p>';
        }
    },

    handleDirectActionSubmit(actionName, details = {}, buttonElement = null) {
        if (isEventActive()) {
            showToast("Please resolve the current event before performing other actions.", "warning");
            if (buttonElement) buttonElement.classList.remove('button-processing'); // Remove if added before check
            return;
        }
        if (DOM.hiddenActionNameInput) DOM.hiddenActionNameInput.value = actionName;
        if (DOM.hiddenDetailsInput) DOM.hiddenDetailsInput.value = JSON.stringify(details);
        if (DOM.actionForm) {
            if (buttonElement) buttonElement.classList.add('button-processing');
            DOM.actionForm.submit();
        }
    },

    // More complex handler for actions that might open forms
    handleActionClick(actionName, buttonElement = null) {
        if (isEventActive()) {
            showToast("Please resolve the current event before performing other actions.", "warning");
            return;
        }
        if (DOM.hiddenActionNameInput) DOM.hiddenActionNameInput.value = actionName;

        switch (actionName) {
            case CONSTANTS.ACTION_NAMES.CRAFT:
                showDynamicForm(DOM.craftDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.BUY_FROM_OWN_SHOP:
                showDynamicForm(DOM.buyDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.SELL_TO_OWN_SHOP:
                UIShopAndInventory.populateSellDropdown();
                showDynamicForm(DOM.sellDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.BUY_FROM_NPC:
                if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.HEMLOCK_HUT) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.HEMLOCK);
                    showDynamicForm(DOM.hemlockHerbsDetailsDiv);
                } else if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.BORIN);
                    showDynamicForm(DOM.borinItemsDetailsDiv);
                }
                break;
            case CONSTANTS.ACTION_NAMES.TALK_TO_BORIN: // Assuming this might lead to buy options
                 if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.BORIN);
                    showDynamicForm(DOM.borinItemsDetailsDiv);
                }
                break;
            case CONSTANTS.ACTION_NAMES.REPAIR_GEAR_BORIN:
                if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateBorinRepairUI();
                    showDynamicForm(DOM.borinRepairDetailsDiv);
                }
                break;
            // Direct submit actions:
            case CONSTANTS.ACTION_NAMES.GATHER_RESOURCES:
            case CONSTANTS.ACTION_NAMES.STUDY_LOCAL_HISTORY:
            case CONSTANTS.ACTION_NAMES.ORGANIZE_INVENTORY:
            case CONSTANTS.ACTION_NAMES.POST_ADVERTISEMENTS:
            case CONSTANTS.ACTION_NAMES.REST_SHORT:
            case CONSTANTS.ACTION_NAMES.REST_LONG:
                this.handleDirectActionSubmit(actionName, {}, buttonElement);
                break;
            default:
                console.warn(`Unhandled action: ${actionName}`);
                // Optionally submit with empty details if it's a generic action not listed
                // this.handleDirectActionSubmit(actionName, {}, buttonElement);
                break;
        }
    },

    populateNpcShopUI(npcName) {
        let targetListDiv, itemsData, selectedItemStateKey, itemNameField;
        if (npcName === CONSTANTS.NPC_NAMES.HEMLOCK) {
            targetListDiv = DOM.hemlockHerbsListDiv;
            itemsData = gameConfigData.hemlockHerbsData;
            selectedItemStateKey = 'selectedHemlockHerbName';
            itemNameField = 'herb-name';
        } else if (npcName === CONSTANTS.NPC_NAMES.BORIN) {
            targetListDiv = DOM.borinItemsListDiv;
            itemsData = gameConfigData.borinItemsData;
            selectedItemStateKey = 'selectedBorinItemName';
            itemNameField = 'item-name';
        } else {
            return;
        }

        window[selectedItemStateKey] = null; // Reset global state for selection, e.g., selectedHemlockHerbName = null;
        if (targetListDiv) {
            targetListDiv.innerHTML = '';
            if (itemsData && Object.keys(itemsData).length > 0) {
                const ul = document.createElement('ul');
                ul.className = 'npc-item-list'; // Add class for styling
                for (const itemKey in itemsData) {
                    const item = itemsData[itemKey];
                    const li = document.createElement('li');
                    // Using template literals for cleaner HTML string construction
                    li.innerHTML = `
                        <strong>${item.name}</strong> - ${item.price}G<br>
                        <em>${item.description}</em><br>
                        <button type="button" class="action-button select-npc-item-button" data-${itemNameField}="${item.name}" data-npc="${npcName}">Select</button>
                    `;
                    ul.appendChild(li);
                }
                targetListDiv.appendChild(ul);
            } else {
                targetListDiv.innerHTML = `<p>No items available from ${npcName}.</p>`;
            }
        }
    },

    populateBorinRepairUI() {
        if (DOM.borinRepairItemSelect) {
            DOM.borinRepairItemSelect.innerHTML = '<option value="">-- Select Item --</option>';
            if (gameConfigData.playerInventoryForSellDropdown && gameConfigData.playerInventoryForSellDropdown.length > 0) {
                gameConfigData.playerInventoryForSellDropdown.forEach(item => {
                    const itemName = (typeof item === 'string') ? item : item.name;
                    if (itemName) {
                        const option = document.createElement('option');
                        option.value = itemName;
                        option.textContent = itemName;
                        DOM.borinRepairItemSelect.appendChild(option);
                    }
                });
            } else {
                DOM.borinRepairItemSelect.innerHTML = '<option value="">-- No items to repair --</option>';
            }
            DOM.borinRepairItemSelect.onchange = function() {
                if (DOM.borinRepairCostDisplay) DOM.borinRepairCostDisplay.textContent = this.value ? "Cost determined by Borin" : "N/A";
            };
            if (DOM.borinRepairCostDisplay) DOM.borinRepairCostDisplay.textContent = "N/A";
        }
    },


    handleDynamicFormSubmit(event) {
        if (isEventActive()) {
            showToast("Please resolve the current event before performing other actions.", "warning");
            // Prevent form submission logic if an event is active.
            // We might also want to remove any 'button-processing' class if it was added.
            const processingButton = event.target.closest('.button-processing');
            if (processingButton) processingButton.classList.remove('button-processing');
            return;
        }
        const targetButton = event.target.closest('.submit-details-button, #submit_buy_hemlock_herb_button, #submit_buy_borin_item_button, #submit-borin-repair-button');
        if (!targetButton) return;

        let details = {};
        let actionName = DOM.hiddenActionNameInput.value; // Should be set by handleActionClick

        if (currentOpenDynamicForm === DOM.craftDetailsDiv) {
            if (DOM.craftItemNameInput && DOM.craftItemNameInput.value) details.item_name = DOM.craftItemNameInput.value;
            actionName = CONSTANTS.ACTION_NAMES.CRAFT;
        } else if (currentOpenDynamicForm === DOM.buyDetailsDiv) {
            if (DOM.buyItemNameInput && DOM.buyItemNameInput.value) details.item_name = DOM.buyItemNameInput.value;
            if (DOM.buyQuantityInput && DOM.buyQuantityInput.value) details.quantity = parseInt(DOM.buyQuantityInput.value, 10);
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_OWN_SHOP;
        } else if (currentOpenDynamicForm === DOM.sellDetailsDiv) {
            if (DOM.sellItemNameInput && DOM.sellItemNameInput.value) details.item_name = DOM.sellItemNameInput.value;
            actionName = CONSTANTS.ACTION_NAMES.SELL_TO_OWN_SHOP;
        } else if (currentOpenDynamicForm === DOM.hemlockHerbsDetailsDiv) {
            if (!selectedHemlockHerbName) { showToast("Please select an herb to buy.", "warning"); return; }
            const quantity = parseInt(DOM.hemlockQuantityInput.value, 10);
            if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
            details = { npc_name: CONSTANTS.NPC_NAMES.HEMLOCK, item_name: selectedHemlockHerbName, quantity: quantity };
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_NPC;
        } else if (currentOpenDynamicForm === DOM.borinItemsDetailsDiv) {
            if (!selectedBorinItemName) { showToast("Please select an item to buy from Borin.", "warning"); return; }
            const quantity = parseInt(DOM.borinQuantityInput.value, 10);
            if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
            details = { npc_name: CONSTANTS.NPC_NAMES.BORIN, item_name: selectedBorinItemName, quantity: quantity };
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_NPC;
        } else if (currentOpenDynamicForm === DOM.borinRepairDetailsDiv) {
            const selectedItemToRepair = DOM.borinRepairItemSelect ? DOM.borinRepairItemSelect.value : null;
            if (!selectedItemToRepair) { showToast("Please select an item to repair.", "warning"); return; }
            details = { item_name_to_repair: selectedItemToRepair };
            actionName = CONSTANTS.ACTION_NAMES.REPAIR_GEAR_BORIN;
        }

        this.handleDirectActionSubmit(actionName, details, targetButton);
    },

    initEventListeners() {
        // Sub-location selection
        if (DOM.subLocationsListDiv) {
            DOM.subLocationsListDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('sub-location-button')) {
                    this.displaySubLocationActions(event.target.dataset.sublocName);
                }
            });
        }

        // Actions within a sub-location
        if (DOM.currentSubLocationActionsListDiv) {
            DOM.currentSubLocationActionsListDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('subloc-action-button')) {
                    this.handleActionClick(event.target.dataset.actionName, event.target);
                }
            });
        }

        // Map travel
        if (DOM.mapDestinationsDiv) {
            DOM.mapDestinationsDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('map-destination-button')) {
                    this.handleDirectActionSubmit(CONSTANTS.ACTION_NAMES.TRAVEL_TO_TOWN, { town_name: event.target.dataset.townName });
                }
            });
        }

        // General action buttons
        const generalActionButtons = [
            { el: DOM.gatherResourcesButton, name: CONSTANTS.ACTION_NAMES.GATHER_RESOURCES },
            { el: DOM.studyLocalHistoryButton, name: CONSTANTS.ACTION_NAMES.STUDY_LOCAL_HISTORY },
            { el: DOM.organizeInventoryButton, name: CONSTANTS.ACTION_NAMES.ORGANIZE_INVENTORY },
            { el: DOM.postAdvertisementsButton, name: CONSTANTS.ACTION_NAMES.POST_ADVERTISEMENTS },
            { el: DOM.shortRestButton, name: CONSTANTS.ACTION_NAMES.REST_SHORT },
            { el: DOM.longRestButton, name: CONSTANTS.ACTION_NAMES.REST_LONG },
        ];
        generalActionButtons.forEach(pair => {
            if (pair.el) {
                pair.el.addEventListener('click', () => this.handleActionClick(pair.name, pair.el));
            }
        });

        // NPC item selection (delegated)
        const handleNpcItemSelect = (event) => {
            const button = event.target.closest('.select-npc-item-button');
            if (!button) return;

            const npcName = button.dataset.npc;
            let selectedItemNameKey, listContainer;

            if (npcName === CONSTANTS.NPC_NAMES.HEMLOCK) {
                selectedHemlockHerbName = button.dataset.herbName;
                listContainer = DOM.hemlockHerbsListDiv;
            } else if (npcName === CONSTANTS.NPC_NAMES.BORIN) {
                selectedBorinItemName = button.dataset.itemName;
                listContainer = DOM.borinItemsListDiv;
            } else {
                return;
            }

            if (listContainer) {
                listContainer.querySelectorAll('.select-npc-item-button').forEach(btn => {
                    btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; // Reset others
                    btn.classList.remove('selected-item-button'); // CSS class instead of inline style
                });
                button.style.fontWeight = 'bold'; // Or use a class:
                button.classList.add('selected-item-button');
            }
        };

        if (DOM.hemlockHerbsListDiv) DOM.hemlockHerbsListDiv.addEventListener('click', handleNpcItemSelect);
        if (DOM.borinItemsListDiv) DOM.borinItemsListDiv.addEventListener('click', handleNpcItemSelect);


        // Submit buttons in dynamic forms (delegated)
        if (DOM.dynamicActionFormsContainer) {
            DOM.dynamicActionFormsContainer.addEventListener('click', (event) => this.handleDynamicFormSubmit(event));
        }

        // Close buttons on dynamic forms
        if (DOM.closeDynamicFormButtons) {
            DOM.closeDynamicFormButtons.forEach(button => {
                button.addEventListener('click', () => {
                    hideAllDynamicForms();
                    if (DOM.currentTownDisplayActions && DOM.currentTownDisplayActions.textContent) {
                        this.displaySubLocations();
                    }
                });
            });
        }

        // Event listeners for item actions (Use, Attune, Unattune)
        // Delegated from a higher-level container for dynamically added items.
        const fullInventoryPanelContent = document.querySelector('#full-inventory-panel-container .full-panel-content');
        if (fullInventoryPanelContent) {
            fullInventoryPanelContent.addEventListener('click', (event) => {
                const target = event.target;
                let actionName = null;
                let details = {};

                if (target.classList.contains('use-item-button')) {
                    actionName = 'USE_ITEM';
                    details.item_name = target.dataset.itemName;
                } else if (target.classList.contains('attune-item-button')) {
                    actionName = 'ATTUNE_ITEM';
                    details.item_name = target.dataset.itemName;
                }
                // Unattune is handled by a different panel, see below.

                if (actionName) {
                    this.handleDirectActionSubmit(actionName, details, target);
                }
            });
        }

        const fullStatsPanelContent = document.querySelector('#full-stats-panel-container .full-panel-content');
        if (fullStatsPanelContent) {
            fullStatsPanelContent.addEventListener('click', (event) => {
                const target = event.target;
                if (target.classList.contains('unattune-item-button')) {
                    const actionName = 'UNATTUNE_ITEM';
                    const details = { item_name: target.dataset.itemName };
                    this.handleDirectActionSubmit(actionName, details, target);
                }
            });
        }
    },

    init() {
        this.initEventListeners();
        // Initial population of sub-locations if town context exists
        if (DOM.currentTownDisplayActions && DOM.currentTownDisplayActions.textContent) {
            this.displaySubLocations();
        } else {
            if (DOM.subLocationsListDiv) DOM.subLocationsListDiv.innerHTML = '<p>No town context.</p>';
        }
    }
};



const UITopMenu = {
    init() {
        if (DOM.topRightMenuButton && DOM.settingsPopup) {
            DOM.topRightMenuButton.addEventListener('click', (event) => {
                event.stopPropagation();
                const isHidden = DOM.settingsPopup.style.display === 'none' || DOM.settingsPopup.style.display === '';
                DOM.settingsPopup.style.display = isHidden ? 'block' : 'none';
                DOM.topRightMenuButton.setAttribute('aria-expanded', isHidden.toString());
            });
        }

        if (DOM.saveGameButton) {
            DOM.saveGameButton.addEventListener('click', () => {
                showToast("Game progress is automatically saved after each action.", "info", 7000);
                if (DOM.settingsPopup) DOM.settingsPopup.style.display = 'none';
                if (DOM.topRightMenuButton) DOM.topRightMenuButton.setAttribute('aria-expanded', 'false');
            });
        }

        document.addEventListener('click', (event) => {
            if (DOM.settingsPopup && DOM.settingsPopup.style.display === 'block') {
                if (!DOM.settingsPopup.contains(event.target) && DOM.topRightMenuButton && !DOM.topRightMenuButton.contains(event.target)) {
                    DOM.settingsPopup.style.display = 'none';
                    if (DOM.topRightMenuButton) DOM.topRightMenuButton.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }
};

const UIInitialPopups = {
    processEventPopup() {
        const { awaitingEventChoice, pendingEventDataJson } = gameConfigData;
        if (awaitingEventChoice && pendingEventDataJson && DOM.eventPopup) {
            try {
                const eventData = JSON.parse(pendingEventDataJson); // Parse the JSON string
                if (DOM.eventPopupNameEl) DOM.eventPopupNameEl.textContent = eventData.name || "An Event Occurs!";
                if (DOM.eventPopupDescriptionEl) DOM.eventPopupDescriptionEl.innerHTML = eventData.description || "You must make a choice.";

                if (DOM.eventPopupChoicesContainer) {
                    DOM.eventPopupChoicesContainer.innerHTML = ''; // Clear
                    if (eventData.choices && eventData.choices.length > 0) {
                        eventData.choices.forEach((choice, index) => {
                            const button = document.createElement('button');
                            button.className = 'event-choice-button action-button';
                            button.dataset.choiceIndex = index;
                            let buttonText = choice.text;
                            if (choice.skill && choice.dc) buttonText += ` <span class="skill-check-indicator">[${choice.skill} DC ${choice.dc}]</span>`;
                            if (choice.item_requirement_desc) buttonText += ` <span class="item-req-indicator">(${choice.item_requirement_desc})</span>`;
                            button.innerHTML = buttonText;
                            DOM.eventPopupChoicesContainer.appendChild(button);
                        });

                        // Event listener for choices (delegated, one-time attach)
                        if (!DOM.eventPopupChoicesContainer.dataset.listenerAttached) {
                            DOM.eventPopupChoicesContainer.addEventListener('click', (event) => {
                                if (event.target.classList.contains('event-choice-button')) {
                                    const choiceIndex = event.target.dataset.choiceIndex;
                                    const currentEventName = eventData.name; // Capture from closure

                                    if (choiceIndex === undefined || !currentEventName) {
                                        console.error("Error: Missing choice index or event name for event submission.");
                                        showToast("Error processing your choice.", "error");
                                        return;
                                    }
                                    // Submit choice via a dynamically created form
                                    const form = document.createElement('form');
                                    form.method = 'POST';
                                    form.action = gameConfigData.submitEventChoiceUrl;
                                    form.innerHTML = `
                                        <input type="hidden" name="event_name" value="${currentEventName}">
                                        <input type="hidden" name="choice_index" value="${choiceIndex}">
                                    `;
                                    document.body.appendChild(form);
                                    form.submit();
                                    if (DOM.eventPopup) DOM.eventPopup.style.display = 'none';
                                }
                            });
                            DOM.eventPopupChoicesContainer.dataset.listenerAttached = 'true';
                        }
                    } else {
                        DOM.eventPopupChoicesContainer.innerHTML = '<p>No choices available for this event.</p>';
                    }
                }
                if (DOM.eventPopup) DOM.eventPopup.style.display = 'block';
                if (DOM.hagglingPopupWrapper) DOM.hagglingPopupWrapper.classList.add('hidden'); // Ensure haggle is hidden if event shows
                document.body.classList.add('event-active'); // Add class to body
            } catch (e) {
                console.error("Error processing event data for popup:", e);
                if (DOM.eventPopup) DOM.eventPopup.style.display = 'none';
                document.body.classList.remove('event-active'); // Ensure class is removed on error
            }
        } else {
            // If no event is active, ensure the class is not on the body
            // This handles cases where the page might load without a pending event
            // after a previous event was resolved.
            document.body.classList.remove('event-active');
        }
    },

    processActionResultToast() {
        const { popupActionResult } = gameConfigData;
        if (popupActionResult && popupActionResult.trim() !== "") {
            const toastMessage = popupActionResult.replace(/<br\s*\/?>/gi, " "); // Flatten <br>
            let actionResultType = 'info';
            const lowerMessage = toastMessage.toLowerCase();
            if (lowerMessage.includes('success')) actionResultType = 'success';
            else if (lowerMessage.includes('fail') || lowerMessage.includes('error') || lowerMessage.includes('not possible')) actionResultType = 'error';
            else if (lowerMessage.includes('warning')) actionResultType = 'warning';
            showToast(toastMessage, actionResultType, 7000);
        }
    },

    processSkillRollToast() {
        const { lastSkillRollStr } = gameConfigData;
        if (lastSkillRollStr && lastSkillRollStr.trim() !== "") {
            let skillRollType = 'info';
            const lowerMessage = lastSkillRollStr.toLowerCase();
            if (lowerMessage.includes('success')) skillRollType = 'success';
            else if (lowerMessage.includes('fail') || lowerMessage.includes('failure')) skillRollType = 'error';
            showToast(lastSkillRollStr, skillRollType, 7000);
        }
    },

    processHagglingPopup() {
        console.log("[UIInitialPopups] processHagglingPopup called.");
        const { hagglingPending, pendingHagglingDataJson } = gameConfigData;
        console.log("[UIInitialPopups] hagglingPending:", hagglingPending);
        console.log("[UIInitialPopups] pendingHagglingDataJson:", pendingHagglingDataJson);

        if (hagglingPending && pendingHagglingDataJson && DOM.hagglingPopupWrapper) {
            console.log("[UIInitialPopups] Conditions met, calling UIHaggling.populateAndShowModal.");
            UIHaggling.populateAndShowModal(pendingHagglingDataJson);
            if (DOM.eventPopup) {
                console.log("[UIInitialPopups] Hiding event popup because haggling popup should show.");
                DOM.eventPopup.style.display = 'none'; // Ensure event popup is hidden
            }
            // If haggling popup is being shown, ensure 'event-active' class is removed from body
            // as haggling should take precedence if it's displayed after an event was processed.
            if (document.body.classList.contains('event-active')) {
                console.log("[UIInitialPopups] Removing 'event-active' class from body as haggling popup is shown.");
                document.body.classList.remove('event-active');
            }
        } else {
            console.log("[UIInitialPopups] Conditions NOT met for haggling popup OR wrapper missing. Ensuring haggling popup is hidden.");
            if (DOM.hagglingPopupWrapper) {
                DOM.hagglingPopupWrapper.classList.add('hidden');
            } else {
                console.log("[UIInitialPopups] Haggling popup wrapper (DOM.hagglingPopupWrapper) not found.");
            }
        }
    },

    init() {
        this.processActionResultToast();
        this.processEventPopup();
        this.processSkillRollToast();
        this.processHagglingPopup(); // Check for haggling state on page load/refresh
    }
};

const UIHaggling = {
    currentHagglingData: null,

    populateAndShowModal(jsonData) { // Renamed data to jsonData for clarity
        console.log("[UIHaggling] populateAndShowModal called with jsonData:", jsonData);

        if (!DOM.hagglingPopupWrapper) {
            console.error("[UIHaggling] Haggling modal wrapper element (DOM.hagglingPopupWrapper) missing. Cannot display haggling popup.");
            return;
        }

        try {
            // Attempt to parse the JSON data first
            if (typeof jsonData === 'string') {
                this.currentHagglingData = JSON.parse(jsonData);
                console.log("[UIHaggling] Successfully parsed jsonData:", this.currentHagglingData);
            } else if (typeof jsonData === 'object' && jsonData !== null) {
                // If it's already an object (e.g., if backend directly passes object in future or for testing)
                this.currentHagglingData = jsonData;
                 console.log("[UIHaggling] jsonData is already an object:", this.currentHagglingData);
            } else {
                // Handles null, undefined, or other non-string/non-object types for jsonData
                console.error("[UIHaggling] populateAndShowModal: Received invalid jsonData type or null/undefined.", jsonData);
                this.currentHagglingData = null; // Ensure it's null if data is bad
            }

            // IMPROVED CHECK: If data is not a valid object or is empty, show a clear error state and bail.
            if (!this.currentHagglingData || typeof this.currentHagglingData !== 'object' || Object.keys(this.currentHagglingData).length === 0) {
                console.error("[UIHaggling] populateAndShowModal: Parsed haggling data is invalid or empty.", this.currentHagglingData);
                if (DOM.hagglingPopupTitle) DOM.hagglingPopupTitle.textContent = "Trade Unavailable";
                if (DOM.haggleItemName) DOM.haggleItemName.textContent = 'Information not available.';
                if (DOM.haggleItemQuality) DOM.haggleItemQuality.textContent = '';
                if (DOM.haggleItemQuantity) DOM.haggleItemQuantity.textContent = '';
                if (DOM.haggleNpcName) DOM.haggleNpcName.textContent = '';
                if (DOM.haggleNpcMood) DOM.haggleNpcMood.textContent = '';
                if (DOM.haggleCurrentOffer) DOM.haggleCurrentOffer.textContent = '';
                if (DOM.haggleTargetPriceInfo) DOM.haggleTargetPriceInfo.classList.add('hidden');
                if (DOM.haggleLastCheckResult) DOM.haggleLastCheckResult.classList.add('hidden');
                if (DOM.haggleRoundsInfo) DOM.haggleRoundsInfo.classList.add('hidden');

                if (DOM.haggleFinalOfferNotice) {
                    DOM.haggleFinalOfferNotice.classList.remove('hidden');
                    DOM.haggleFinalOfferNotice.textContent = "There was a problem loading trade details. Please close this window.";
                }

                if (DOM.haggleAcceptButton) DOM.haggleAcceptButton.disabled = true;
                if (DOM.hagglePersuadeButton) DOM.hagglePersuadeButton.disabled = true;
                if (DOM.haggleDeclineButton) {
                    DOM.haggleDeclineButton.disabled = false;
                    // Consider changing button text to "Close" and action to UIHaggling.closeModal() for this specific error state.
                    // For now, existing decline logic will run, which attempts backend communication.
                }
                // Avoid calling showToast if it was already called by processHagglingPopup for this condition.
                // showToast("Error with trade data. The trade window cannot be shown correctly.", "error");
                return; // Modal remains hidden if error occurs here
            }

            // If data is valid, now show the modal
            if (DOM.hagglingPopup) {
                DOM.hagglingPopup.style.display = 'block';
            }
            DOM.hagglingPopupWrapper.classList.remove('hidden');
            console.log("[UIHaggling] Haggling popup wrapper 'hidden' class removed.");
            DOM.hagglingPopup.setAttribute('aria-hidden', 'false');

            // Explicitly remove event-active class from body if haggling modal is successfully shown
            if (document.body.classList.contains('event-active')) {
                console.log("[UIHaggling] Removing 'event-active' class from body as haggling popup is shown.");
                document.body.classList.remove('event-active');
            }

            const {
                item_name, item_quality, quantity, npc_name, npc_mood, current_offer,
                player_target_price, shop_target_price, haggle_rounds_attempted,
                max_haggle_rounds, can_still_haggle, last_skill_check_result, context
            } = this.currentHagglingData;

            // Secondary check for essential keys, which might indicate a partially valid object.
            if (item_name === undefined || npc_name === undefined || current_offer === undefined || quantity === undefined || context === undefined) {
                console.error("[UIHaggling] populateAndShowModal: Haggling data object is missing essential keys.", this.currentHagglingData);
                if (DOM.hagglingPopupTitle) DOM.hagglingPopupTitle.textContent = "Trade Data Error";
                if (DOM.haggleItemName) DOM.haggleItemName.textContent = item_name === undefined ? 'Item Error' : (item_name || 'N/A');
                if (DOM.haggleItemQuality) DOM.haggleItemQuality.textContent = item_quality || 'N/A';
                if (DOM.haggleItemQuantity) DOM.haggleItemQuantity.textContent = quantity === undefined ? 'Qty Error' : (quantity || 'N/A');
                if (DOM.haggleNpcName) DOM.haggleNpcName.textContent = npc_name === undefined ? 'NPC Error' : (npc_name || 'Mysterious Figure');
                if (DOM.haggleCurrentOffer) DOM.haggleCurrentOffer.textContent = `${current_offer === undefined ? 'Price Error' : (current_offer || 0)}g`;

                if (DOM.haggleFinalOfferNotice) {
                    DOM.haggleFinalOfferNotice.classList.remove('hidden');
                    DOM.haggleFinalOfferNotice.textContent = "A problem occurred with trade details. Please decline.";
                }
                if (DOM.haggleAcceptButton) DOM.haggleAcceptButton.disabled = true;
                if (DOM.hagglePersuadeButton) DOM.hagglePersuadeButton.disabled = true;
                if (DOM.haggleDeclineButton) DOM.haggleDeclineButton.disabled = false;
                showToast("Error in trade details. Please decline.", "error");
                return;
            }

            if (DOM.haggleItemName) DOM.haggleItemName.textContent = item_name || 'N/A';
            if (DOM.haggleItemQuality) DOM.haggleItemQuality.textContent = item_quality || 'N/A';
            if (DOM.haggleItemQuantity) DOM.haggleItemQuantity.textContent = quantity !== undefined ? quantity : '1';
            if (DOM.haggleNpcName) DOM.haggleNpcName.textContent = npc_name || 'Mysterious Figure';
            if (DOM.haggleNpcMood) DOM.haggleNpcMood.textContent = npc_mood || 'Neutral';
            if (DOM.haggleCurrentOffer) DOM.haggleCurrentOffer.textContent = `${current_offer || 0}g`;

            if (DOM.haggleTargetPriceInfo) {
                DOM.haggleTargetPriceInfo.classList.remove('hidden');
                const playerTargetEl = DOM.hagglePlayerTargetPrice ? DOM.hagglePlayerTargetPrice.parentElement : null;
                const shopTargetEl = DOM.haggleShopTargetPrice ? DOM.haggleShopTargetPrice.parentElement : null;

                if (context === "player_buying" && player_target_price !== undefined) {
                    if (DOM.hagglePlayerTargetPrice) DOM.hagglePlayerTargetPrice.textContent = `${player_target_price}g`;
                    if (playerTargetEl) playerTargetEl.classList.remove('hidden');
                    if (shopTargetEl) shopTargetEl.classList.add('hidden');
                } else if (context === "player_selling" && shop_target_price !== undefined) {
                    if (DOM.haggleShopTargetPrice) DOM.haggleShopTargetPrice.textContent = `${shop_target_price}g`;
                    if (shopTargetEl) shopTargetEl.classList.remove('hidden');
                    if (playerTargetEl) playerTargetEl.classList.add('hidden');
                } else {
                    if (playerTargetEl) playerTargetEl.classList.add('hidden');
                    if (shopTargetEl) shopTargetEl.classList.add('hidden');
                    DOM.haggleTargetPriceInfo.classList.add('hidden');
                }
            }

            if (DOM.haggleLastCheckResult && DOM.haggleLastCheckText) {
                if (last_skill_check_result) {
                    DOM.haggleLastCheckText.textContent = last_skill_check_result;
                    DOM.haggleLastCheckResult.classList.remove('hidden');
                } else {
                    DOM.haggleLastCheckResult.classList.add('hidden');
                }
            }

            if (DOM.haggleCurrentRound) DOM.haggleCurrentRound.textContent = haggle_rounds_attempted !== undefined ? haggle_rounds_attempted : 0;
            if (DOM.haggleMaxRounds) DOM.haggleMaxRounds.textContent = max_haggle_rounds !== undefined ? max_haggle_rounds : 3;
            if (DOM.haggleRoundsInfo) DOM.haggleRoundsInfo.classList.remove('hidden');

            const finalOffer = !can_still_haggle || (haggle_rounds_attempted >= max_haggle_rounds);
            if (DOM.hagglePersuadeButton) DOM.hagglePersuadeButton.disabled = finalOffer;
            if (DOM.haggleAcceptButton) DOM.haggleAcceptButton.disabled = false;
            if (DOM.haggleDeclineButton) DOM.haggleDeclineButton.disabled = false;
            if (DOM.haggleFinalOfferNotice) DOM.haggleFinalOfferNotice.classList.toggle('hidden', !finalOffer);
            if (DOM.haggleFinalOfferNotice && !finalOffer) DOM.haggleFinalOfferNotice.textContent = "This is their final offer.";

            if (DOM.hagglingPopupTitle) {
                DOM.hagglingPopupTitle.textContent = context === "player_buying" ? `Buy from ${npc_name || 'NPC'}` : `Sell to ${npc_name || 'NPC'}`;
            }

            if (DOM.haggleAcceptButton) DOM.haggleAcceptButton.focus();

        } catch (error) {
            console.error("Error populating haggling modal:", error);
            showToast("A critical error occurred displaying trade details. Please decline.", "error");
            // Attempt to set a very basic error state in the modal
            if (DOM.hagglingPopupTitle) DOM.hagglingPopupTitle.textContent = "Critical Display Error";
            if (DOM.haggleItemName) DOM.haggleItemName.textContent = "Error";
            if (DOM.haggleNpcName) DOM.haggleNpcName.textContent = "Error";
            if (DOM.haggleItemQuantity) DOM.haggleItemQuantity.textContent = "N/A";
            if (DOM.haggleCurrentOffer) DOM.haggleCurrentOffer.textContent = "N/A";

            if (DOM.haggleAcceptButton) DOM.haggleAcceptButton.disabled = true;
            if (DOM.hagglePersuadeButton) DOM.hagglePersuadeButton.disabled = true;
            if (DOM.haggleDeclineButton) DOM.haggleDeclineButton.disabled = false; // Ensure decline is usable
        }
    },

    closeModal() {
        if (DOM.hagglingPopupWrapper) {
            DOM.hagglingPopupWrapper.classList.add('hidden');
            if(DOM.hagglingPopup) {
                DOM.hagglingPopup.setAttribute('aria-hidden', 'true');
                DOM.hagglingPopup.style.display = 'none'; // Also hide it directly
            }
        }
        this.currentHagglingData = null;
    },

    handleChoice(choiceType) {
        console.log("[UIHaggling.handleChoice] Called with choiceType:", choiceType);

        const eventActive = isEventActive();
        console.log("[UIHaggling.handleChoice] isEventActive() returned:", eventActive);
        if (eventActive) {
            showToast("Please resolve the current game event before continuing to haggle.", "warning");
            console.log("[UIHaggling.handleChoice] Exiting because isEventActive() is true.");
            return;
        }

        // If the choice is 'decline' and the UI is in an error state (or any state),
        // we should try to submit a decline action to the backend to clear the session there.
        // If currentHagglingData is truly corrupt, the backend might reject it, but it's worth trying.
        if (choiceType === 'decline') {
            console.log("[UIHaggling.handleChoice] Processing 'decline'. Current haggling data:", this.currentHagglingData);
            // Try to determine context even if data is partial, default if not possible
            const context = (this.currentHagglingData && this.currentHagglingData.context)
                            ? this.currentHagglingData.context
                            : "player_selling"; // Default context for decline if unknown
            console.log("[UIHaggling.handleChoice] Decline context determined as:", context);
            const actionName = context === "player_buying" ?
                               "PROCESS_PLAYER_HAGGLE_CHOICE_BUY" :
                               "PROCESS_PLAYER_HAGGLE_CHOICE_SELL";
            const details = { haggle_choice: "decline" };

            if (DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
                DOM.hiddenActionNameInput.value = actionName;
                DOM.hiddenDetailsInput.value = JSON.stringify(details);
                // It's possible actionForm.submit() itself fails if other JS is broken.
                try {
                    DOM.actionForm.submit();
                } catch (e) {
                    console.error("Error submitting decline action:", e);
                    showToast("Error submitting decline. Closing modal.", "error");
                    this.closeModal(); // Close UI side if submit fails catastrophically
                }
            } else {
                console.error("Action form elements missing for haggling decline. Closing modal locally.");
                this.closeModal(); // Close UI side if form elements are missing
            }
            return; // Decline action submitted (or attempted)
        }

        // For 'accept' or 'persuade', we absolutely need valid currentHagglingData
        console.log("[UIHaggling.handleChoice] Validating currentHagglingData for accept/persuade. Data:", this.currentHagglingData);
        if (!this.currentHagglingData || typeof this.currentHagglingData !== 'object' || !this.currentHagglingData.context) {
            console.error("[UIHaggling.handleChoice] No valid haggling session data to process choice (accept/persuade). Current data:", this.currentHagglingData);
            showToast("Cannot process action due to missing trade data. Please decline.", "error");
            // Do not close modal here, let user explicitly decline the error state.
            return;
        }

        const actionName = this.currentHagglingData.context === "player_buying" ?
                           "PROCESS_PLAYER_HAGGLE_CHOICE_BUY" :
                           "PROCESS_PLAYER_HAGGLE_CHOICE_SELL";
        console.log("[UIHaggling.handleChoice] Determined actionName:", actionName);

        const details = {
            haggle_choice: choiceType,
            // Backend uses self.active_haggling_session
        };
        console.log("[UIHaggling.handleChoice] Prepared details for submission:", details);

        if (DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            console.log("[UIHaggling.handleChoice] Form elements found. Setting values and submitting.");
            DOM.hiddenActionNameInput.value = actionName;
            DOM.hiddenDetailsInput.value = JSON.stringify(details);
            DOM.actionForm.submit();
            // Backend response will update or close the modal.
        } else {
            console.error("[UIHaggling.handleChoice] Action form elements missing for haggling submission (accept/persuade).");
            console.log("[UIHaggling.handleChoice] DOM.actionForm:", DOM.actionForm);
            console.log("[UIHaggling.handleChoice] DOM.hiddenActionNameInput:", DOM.hiddenActionNameInput);
            console.log("[UIHaggling.handleChoice] DOM.hiddenDetailsInput:", DOM.hiddenDetailsInput);
            showToast("Error submitting haggle choice.", "error");
            this.closeModal(); // Fallback close
        }
    },

    init() {
        console.log("[UIHaggling.init] Called."); // Added log
        if (DOM.hagglingChoicesContainer) {
            console.log("[UIHaggling.init] Found DOM.hagglingChoicesContainer, attaching listener:", DOM.hagglingChoicesContainer);
            DOM.hagglingChoicesContainer.addEventListener('click', (event) => {
                console.log("[UIHaggling.init] Click detected on hagglingChoicesContainer. Event target:", event.target);
                const button = event.target.closest('.haggle-choice-button');
                console.log("[UIHaggling.init] Button found by .closest():", button);
                if (button && button.dataset.choice) {
                    console.log("[UIHaggling.init] Button has .haggle-choice-button class and data-choice. Calling handleChoice with:", button.dataset.choice);
                    this.handleChoice(button.dataset.choice);
                } else {
                    console.log("[UIHaggling.init] Clicked, but not on a valid haggle-choice-button or button missing data-choice.");
                    if (button) {
                        console.log("[UIHaggling.init] Button was found, but missing data-choice. Button:", button, "Dataset:", button.dataset);
                    }
                }
            });
        }

        // Close modal with Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && DOM.hagglingPopupWrapper && !DOM.hagglingPopupWrapper.classList.contains('hidden')) {
                // For haggling, Escape should probably mean "Decline" or just close without action if no decline button.
                // Let's make it behave like clicking decline.
                this.handleChoice('decline');
            }
        });
         // Close modal if clicking outside of it (on the wrapper/overlay)
        if (DOM.hagglingPopupWrapper) {
            DOM.hagglingPopupWrapper.addEventListener('click', (event) => {
                if (event.target === DOM.hagglingPopupWrapper) {
                     this.handleChoice('decline'); // Treat as decline
                }
            });
        }

        // Initial check on page load
        if (gameConfigData.hagglingPending && gameConfigData.pendingHagglingDataJson) {
            this.populateAndShowModal(gameConfigData.pendingHagglingDataJson);
        } else {
            this.closeModal(); // Ensure it's hidden if no data
        }
};

const UIInventoryCues = {
    updatePlayerInventoryCues() {
        if (!DOM.playerInventoryGrid || !gameConfigData.playerInventory) {
            return;
        }

        const itemCards = DOM.playerInventoryGrid.querySelectorAll('.inventory-item-card');
        itemCards.forEach(card => {
            const itemNameElement = card.querySelector('.item-name');
            if (!itemNameElement) return;

            const itemName = itemNameElement.textContent.trim().split(' (x')[0]; // Get base item name
            const itemData = gameConfigData.playerInventory.find(item => item.name === itemName);

            if (!itemData) return;

            // Reset cues
            card.classList.remove('attuned-item', 'magical-item', 'is-consumable');

            // Apply Attuned Cue
            if (gameConfigData.playerAttunedItemNames && gameConfigData.playerAttunedItemNames.includes(itemName)) {
                card.classList.add('attuned-item');
            }

            // Apply Magical Cue (assuming itemData has an is_magical property)
            if (itemData.is_magical) {
                card.classList.add('magical-item');
            }

            // Apply Consumable Cue
            if (itemData.is_consumable) {
                card.classList.add('is-consumable');
            }
        });
    },

    init() {
        // Call initially on load if player inventory is present
        this.updatePlayerInventoryCues();
        // This function should also be called after any action that modifies inventory or attunement status.
        // This can be done by ensuring gameConfigData is updated and then calling this,
        // or by having actions emit an event that triggers this update.
        // For now, we rely on page reload/update post-action to refresh gameConfigData.
    }
};
// --- End of UIInventoryCues ---

const UIItemDetailsModal = {
    modalWrapper: null,
    modalElement: null,
    closeButton: null,
    itemNameEl: null,
    itemIconEl: null,
    itemDescriptionEl: null,
    itemTypeEl: null,
    itemQualityEl: null,
    itemValueEl: null,
    itemWeightEl: null,
    itemQuantityEl: null,
    itemEffectsListEl: null,
    itemActionsContainerEl: null,

    initElements() {
        this.modalWrapper = DOM.itemDetailsModalWrapper; // Assuming cached in main DOM object
        this.modalElement = DOM.itemDetailsModal;
        this.closeButton = DOM.closeItemDetailsModal;
        this.itemNameEl = DOM.itemDetailsName;
        this.itemIconEl = DOM.itemDetailsIcon; // Placeholder for now
        this.itemDescriptionEl = DOM.itemDetailsDescription;
        this.itemTypeEl = DOM.itemDetailsType;
        this.itemQualityEl = DOM.itemDetailsQuality;
        this.itemValueEl = DOM.itemDetailsValue;
        this.itemWeightEl = DOM.itemDetailsWeight;
        this.itemQuantityEl = DOM.itemDetailsQuantity;
        this.itemEffectsListEl = DOM.itemDetailsEffectsList;
        this.itemActionsContainerEl = DOM.itemDetailsActionsContainer;

        if (this.closeButton) {
            this.closeButton.addEventListener('click', () => this.hide());
        }
        if (this.modalWrapper) {
            this.modalWrapper.addEventListener('click', (event) => {
                if (event.target === this.modalWrapper) {
                    this.hide();
                }
            });
        }
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modalWrapper && !this.modalWrapper.classList.contains('hidden')) {
                this.hide();
            }
        });
    },

    populateAndShow(itemData, context = 'player_inventory') { // context can be 'player_inventory' or 'shop_inventory'
        if (!this.modalWrapper || !itemData) {
            console.error("Item Details Modal wrapper not found or no item data provided.");
            return;
        }

        // Populate basic info
        if (this.itemNameEl) this.itemNameEl.textContent = itemData.name || 'Unknown Item';
        if (this.itemDescriptionEl) this.itemDescriptionEl.textContent = itemData.description || 'No description available.';
        if (this.itemTypeEl) this.itemTypeEl.textContent = itemData.item_type || 'N/A';
        if (this.itemQualityEl) this.itemQualityEl.textContent = itemData.quality || 'N/A';
        if (this.itemValueEl) this.itemValueEl.textContent = (itemData.base_value !== undefined) ? `${itemData.base_value} G` : 'N/A';
        if (this.itemWeightEl) this.itemWeightEl.textContent = (itemData.weight !== undefined) ? `${itemData.weight} lbs` : 'N/A'; // Assuming weight property exists
        if (this.itemQuantityEl) this.itemQuantityEl.textContent = (itemData.quantity !== undefined) ? itemData.quantity : '1';

        // Populate effects
        if (this.itemEffectsListEl) {
            this.itemEffectsListEl.innerHTML = ''; // Clear previous
            if (itemData.effects && Object.keys(itemData.effects).length > 0) {
                for (const [effectKey, effectValue] of Object.entries(itemData.effects)) {
                    const li = document.createElement('li');
                    let effectText = `${effectKey.replace(/_/g, ' ')}: `;
                    if (typeof effectValue === 'object') {
                        effectText += JSON.stringify(effectValue); // Simple stringify for complex effects
                    } else {
                        effectText += effectValue;
                    }
                    li.textContent = effectText;
                    this.itemEffectsListEl.appendChild(li);
                }
            } else {
                this.itemEffectsListEl.innerHTML = '<li role="listitem">No special effects.</li>';
            }
        }

        // Placeholder for action buttons - Part 2 will handle this
        if (this.itemActionsContainerEl) {
            this.itemActionsContainerEl.innerHTML = ''; // Clear previous buttons

            const createActionButton = (text, action, itemDetails, additionalClasses = []) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = ['action-button', ...additionalClasses].join(' ');
                button.textContent = text;
                button.dataset.action = action;
                button.dataset.itemName = itemData.name; // Always include item name

                // Add more item details if needed for the action
                if (itemDetails) {
                    Object.entries(itemDetails).forEach(([key, value]) => {
                        button.dataset[key] = value;
                    });
                }

                button.addEventListener('click', () => {
                    // Use UIActionsAndEvents.handleDirectActionSubmit for consistency
                    // This assumes all modal actions are "direct" and don't open further forms from within the modal itself
                    const actionDetails = { item_name: itemData.name };
                    // Add any other specific details from button.dataset if necessary
                    // For USE_ITEM, ATTUNE_ITEM, UNATTUNE_ITEM, item_name is usually enough.
                    UIActionsAndEvents.handleDirectActionSubmit(action, actionDetails, button);
                    this.hide(); // Close modal after action
                });
                this.itemActionsContainerEl.appendChild(button);
            };

            let hasActions = false;

            // Determine actions based on item properties and context
            if (context === 'player_inventory') {
                if (itemData.is_consumable) {
                    createActionButton('Use Item', 'USE_ITEM');
                    hasActions = true;
                }
                if (itemData.is_attunement) {
                    const isAttuned = gameConfigData.playerAttunedItemNames && gameConfigData.playerAttunedItemNames.includes(itemData.name);
                    if (isAttuned) {
                        createActionButton('Unattune Item', 'UNATTUNE_ITEM');
                        hasActions = true;
                    } else {
                        const slotsUsed = gameConfigData.playerAttunementSlotsUsed !== undefined ? gameConfigData.playerAttunementSlotsUsed : 0;
                        const slotsMax = gameConfigData.playerAttunementSlotsMax !== undefined ? gameConfigData.playerAttunementSlotsMax : 3;
                        if (slotsUsed < slotsMax) {
                            createActionButton('Attune Item', 'ATTUNE_ITEM');
                        } else {
                            const button = document.createElement('button');
                            button.type = 'button';
                            button.className = 'action-button disabled-action-button';
                            button.textContent = 'Attune Item (Slots Full)';
                            button.disabled = true;
                            this.itemActionsContainerEl.appendChild(button);
                        }
                        hasActions = true;
                    }
                }
                // Future: Add "Equip", "Sell to Shop", "Drop" buttons here
            } else if (context === 'shop_inventory') {
                // Future: Add "Buy from Shop", "Haggle" buttons here
                // For now, the old "Buy" button on shop item cards is still active.
                // If we want the modal to handle buying, this is where it would go.
                // Example: createActionButton(`Buy (${itemData.base_value} G)`, 'BUY_FROM_ACTIVE_SHOP'); hasActions = true;
            }


            if (!hasActions) {
                this.itemActionsContainerEl.innerHTML = '<p>No specific actions available for this item in this context.</p>';
            }
        }

        // Show the modal
        this.modalWrapper.classList.remove('hidden');
        if (this.modalElement) this.modalElement.setAttribute('aria-hidden', 'false');
        if (this.closeButton) this.closeButton.focus(); // Focus the close button for accessibility
    },

    hide() {
        if (this.modalWrapper) {
            this.modalWrapper.classList.add('hidden');
        }
        if (this.modalElement) {
            this.modalElement.setAttribute('aria-hidden', 'true');
        }
    },

    init() {
        // Elements will be cached by main cacheDomElements, just need to assign them here
        // This init is more for setting up listeners on the modal itself
    }
};
// --- End of UIItemDetailsModal ---


// --- DOM ELEMENT REFERENCES (grouped by functionality) ---
// Populated in `cacheDomElements`
const DOM = {};

function cacheDomElements() {
    // ... (existing cacheDomElements content) ...
    DOM.itemDetailsModalWrapper = document.getElementById('item-details-modal-wrapper');
    DOM.itemDetailsModal = document.getElementById('item-details-modal');
    DOM.closeItemDetailsModal = document.getElementById('close-item-details-modal');
    DOM.itemDetailsName = document.getElementById('item-details-name');
    DOM.itemDetailsIcon = document.getElementById('item-details-icon');
    DOM.itemDetailsDescription = document.getElementById('item-details-description');
    DOM.itemDetailsType = document.getElementById('item-details-type');
    DOM.itemDetailsQuality = document.getElementById('item-details-quality');
    DOM.itemDetailsValue = document.getElementById('item-details-value');
    DOM.itemDetailsWeight = document.getElementById('item-details-weight');
    DOM.itemDetailsQuantity = document.getElementById('item-details-quantity');
    DOM.itemDetailsEffectsList = document.getElementById('item-details-effects-list');
    DOM.itemDetailsActionsContainer = document.getElementById('item-details-actions-container');

    // Inventory grids for attaching click listeners
    DOM.playerInventoryGrid = document.querySelector('.player-inventory-grid');
    DOM.shopInventoryGrid = document.querySelector('.shop-inventory-grid');
    // ... (rest of existing cacheDomElements content) ...
}

// ... (rest of the file, including UIActionsAndEvents.initEventListeners) ...

// Modify UIActionsAndEvents.initEventListeners to open the new modal
// This requires finding the existing function and adding to it.
// For this tool, I'll define a new initEventListeners or assume it's being replaced.

const UIActionsAndEvents = {
    // ... (keep existing methods like displaySubLocations, handleDirectActionSubmit, etc.) ...

    initEventListeners() {
        // ... (existing listeners for sub-locations, map, general actions, dynamic forms etc.) ...

        // --- New/Modified Inventory Item Click Handling ---
        const handleInventoryItemClick = (event, inventorySource) => {
            const itemCard = event.target.closest('.inventory-item-card');
            if (!itemCard) return;

            // Prevent buttons inside the card from also triggering the modal for the card itself
            if (event.target.tagName === 'BUTTON' || event.target.closest('button')) {
                // If the click was on a button (like Use, Attune, Buy), let its specific handler work.
                // The old "Buy" button on shop items might now be part of the modal,
                // or it could remain for quick buy. For now, let's assume modal is primary.
                // If it's a "Buy" button from shop inventory, it might still work as before or also open modal.
                // This part needs careful integration with existing button logic.
                // For now, let's assume all clicks on the card (not specific inner buttons) open the modal.
                if (event.target.classList.contains('use-item-button') ||
                    event.target.classList.contains('attune-item-button') ||
                    event.target.classList.contains('unattune-item-button') ||
                    event.target.classList.contains('buy-item-button')) { // Keep existing buy button functionality for now
                    // Let existing specific button handlers in the full panel inventory take care of it.
                    // This new modal is an alternative way to interact.
                    // However, the plan was to replace small buttons with this modal.
                    // So, we'll need to decide if old buttons are removed or coexist.
                    // For now, let's assume the primary interaction will be via the new modal.
                    // We will trigger the modal, and the modal will have its own action buttons.
                    // The small "Use", "Attune" buttons on the cards will be phased out or hidden by CSS if this modal is preferred.
                }
            }

            const itemName = itemCard.querySelector('.item-name') ? itemCard.querySelector('.item-name').textContent.trim().split(' (x')[0] : null;
            if (!itemName) {
                console.warn("Could not determine item name from card.");
                return;
            }

            let itemData = null;
            if (inventorySource === 'player') {
                itemData = gameConfigData.playerInventory.find(item => item.name === itemName);
            } else if (inventorySource === 'shop') {
                // Assuming shop_inventory is structured similarly, might need adjustment
                // gameConfigData.shopInventory might be just names, or full objects.
                // This needs to be checked against how app.py provides shop_inventory.
                // For now, let's assume it's an array of item objects like playerInventory.
                // If not, this part needs to fetch full item details.
                // Based on index.html: {% for item in shop_inventory %} ... {{ item.name }}
                // This implies shop_inventory IS an array of objects.
                itemData = gameConfigData.shopInventory.find(item => item.name === itemName);
            }


            if (itemData) {
                UIItemDetailsModal.populateAndShow(itemData, inventorySource === 'player' ? 'player_inventory' : 'shop_inventory');
            } else {
                console.warn(`Item data not found for "${itemName}" in ${inventorySource} inventory.`);
                showToast(`Details for ${itemName} could not be loaded.`, 'error');
            }
        };

        if (DOM.playerInventoryGrid) {
            DOM.playerInventoryGrid.addEventListener('click', (event) => handleInventoryItemClick(event, 'player'));
        }
        if (DOM.shopInventoryGrid) { // Assuming shop items also use this modal
            DOM.shopInventoryGrid.addEventListener('click', (event) => handleInventoryItemClick(event, 'shop'));
        }


        // Keep existing event listeners for item actions from the full inventory panel for now
        // These are for the buttons that are NOT inside the new modal.
        const fullInventoryPanelContent = document.querySelector('#full-inventory-panel-container .full-panel-content');
        if (fullInventoryPanelContent) {
            fullInventoryPanelContent.addEventListener('click', (event) => {
                const target = event.target;
                let actionName = null;
                let details = {};

                if (target.classList.contains('use-item-button')) { // These are the old buttons
                    actionName = 'USE_ITEM';
                    details.item_name = target.dataset.itemName;
                } else if (target.classList.contains('attune-item-button')) { // Old button
                    actionName = 'ATTUNE_ITEM';
                    details.item_name = target.dataset.itemName;
                }
                // Buy button is also handled here from shop inventory grid (old way)

                if (actionName) {
                    this.handleDirectActionSubmit(actionName, details, target);
                }
            });
        }
        // ... (rest of existing initEventListeners)
    },

    init() {
        this.initEventListeners();
        if (DOM.currentTownDisplayActions && DOM.currentTownDisplayActions.textContent) {
            this.displaySubLocations();
        } else {
            if (DOM.subLocationsListDiv) DOM.subLocationsListDiv.innerHTML = '<p>No town context.</p>';
        }
    }
};

// --- MAIN INITIALIZATION ---
function main() {
    document.body.classList.add('js-loaded');
    cacheDomElements();
    loadConfigData();

    UIItemDetailsModal.initElements(); // Initialize elements for the new modal
    UIPanels.init();
    UIBottomTabs.init();
    UITopMenu.init();
    UISkillAllocation.init();
    UIAsiFeatChoice.init();
    UIHaggling.init();
    UIInventoryCues.init(); // Initialize inventory cues

    if (DOM.actionForm) {
        UIActionsAndEvents.init(); // This will now include the modified item click handlers
        UIShopAndInventory.init();
    }

    UIInitialPopups.init();

    if (DOM.fullPanelContainers) {
        DOM.fullPanelContainers.forEach(panel => {
            panel.classList.add('hidden');
            const miniPanel = document.querySelector(`[aria-controls="${panel.id}"]`);
            if (miniPanel) {
                miniPanel.setAttribute('aria-expanded', 'false');
            }
        });
        // Ensure Item Details Modal is also hidden initially if not covered by the loop
        if (DOM.itemDetailsModalWrapper && !DOM.itemDetailsModalWrapper.classList.contains('hidden')) {
             DOM.itemDetailsModalWrapper.classList.add('hidden');
        }
    }
    }
};


const UISkillAllocation = {
    populateSkillAllocationModal() {
        if (!DOM.skillAllocationChoicesContainer || !DOM.skillPointsAvailableModalDisplay || !gameConfigData.characterAttributeDefinitions) {
            console.error("Skill allocation modal elements or config data missing.");
            return;
        }

        DOM.skillAllocationChoicesContainer.innerHTML = ''; // Clear previous buttons
        const pointsAvailable = gameConfigData.playerSkillPointsToAllocate || 0;
        DOM.skillPointsAvailableModalDisplay.textContent = pointsAvailable;

        if (pointsAvailable <= 0) {
            DOM.skillAllocationChoicesContainer.innerHTML = '<p>No skill points available to allocate.</p>';
            // Optionally disable the open button or hide the modal trigger if points are zero.
            // For now, the modal will show this message if opened with zero points.
            return;
        }

        const skills = Object.keys(gameConfigData.characterAttributeDefinitions);
        skills.sort(); // Sort skills alphabetically for consistent display

        skills.forEach(skillName => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'action-button skill-allocation-choice-button';
            button.dataset.skillName = skillName;

            const currentBonus = gameConfigData.playerChosenSkillBonuses[skillName] || 0;
            button.textContent = `${skillName} (+${currentBonus})`;
            // Add ARIA label for better accessibility, e.g., "Allocate point to Acrobatics, current bonus +0"
            button.setAttribute('aria-label', `Allocate point to ${skillName}, current bonus +${currentBonus}`);

            DOM.skillAllocationChoicesContainer.appendChild(button);
        });
    },

    openSkillAllocationModal() {
        if (DOM.skillAllocationPopupWrapper && DOM.skillAllocationPopup) {
            this.populateSkillAllocationModal(); // Repopulate each time to reflect current points/bonuses
            DOM.skillAllocationPopupWrapper.classList.remove('hidden');
            DOM.skillAllocationPopup.classList.remove('hidden'); // Ensure modal itself is visible if wrapper controls it
            DOM.skillAllocationPopup.setAttribute('aria-hidden', 'false');
            // Focus the first interactive element in the modal if available
            const firstButton = DOM.skillAllocationChoicesContainer.querySelector('button');
            if (firstButton) {
                firstButton.focus();
            } else if (DOM.closeSkillAllocationPopupButton) {
                DOM.closeSkillAllocationPopupButton.focus();
            }
        }
    },

    closeSkillAllocationModal() {
        if (DOM.skillAllocationPopupWrapper && DOM.skillAllocationPopup) {
            DOM.skillAllocationPopupWrapper.classList.add('hidden');
            DOM.skillAllocationPopup.classList.add('hidden');
            DOM.skillAllocationPopup.setAttribute('aria-hidden', 'true');
            if (DOM.allocateSkillPointsButton) { // Return focus to the button that opened the modal
                DOM.allocateSkillPointsButton.focus();
            }
        }
    },

    handleSkillChoiceClick(event) {
        if (isEventActive()) {
            // This check is theoretically not essential if the skill allocation modal itself is blocked by event-active CSS,
            // but it's good for defense-in-depth.
            showToast("Please resolve the current game event before allocating skill points.", "warning");
            return;
        }
        if (event.target.classList.contains('skill-allocation-choice-button')) {
            const skillName = event.target.dataset.skillName;
            if (skillName && DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
                DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.ALLOCATE_SKILL_POINT;
                DOM.hiddenDetailsInput.value = JSON.stringify({ skill_name: skillName });
                DOM.actionForm.submit();
                this.closeSkillAllocationModal(); // Close modal after submission
            } else {
                console.error("Skill name or form elements missing for skill allocation submission.");
                showToast("Error submitting skill allocation.", "error");
            }
        }
    },

    init() {
        if (DOM.allocateSkillPointsButton) {
            DOM.allocateSkillPointsButton.addEventListener('click', () => this.openSkillAllocationModal());
        }
        if (DOM.closeSkillAllocationPopupButton) {
            DOM.closeSkillAllocationPopupButton.addEventListener('click', () => this.closeSkillAllocationModal());
        }
        if (DOM.skillAllocationChoicesContainer) {
            DOM.skillAllocationChoicesContainer.addEventListener('click', (event) => this.handleSkillChoiceClick(event));
        }
        // Close modal if clicking outside of it (on the wrapper/overlay)
        if (DOM.skillAllocationPopupWrapper) {
            DOM.skillAllocationPopupWrapper.addEventListener('click', (event) => {
                if (event.target === DOM.skillAllocationPopupWrapper) {
                    this.closeSkillAllocationModal();
                }
            });
        }
        // Close modal with Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && DOM.skillAllocationPopupWrapper && !DOM.skillAllocationPopupWrapper.classList.contains('hidden')) {
                this.closeSkillAllocationModal();
            }
        });
    }
};


// --- MAIN INITIALIZATION ---
function main() {
    document.body.classList.add('js-loaded');
    cacheDomElements(); // Populate DOM object
    loadConfigData(); // Populate gameConfigData object

    UIPanels.init();
    UIBottomTabs.init();
    UITopMenu.init();
    UISkillAllocation.init();
    UIAsiFeatChoice.init(); // Initialize ASI/Feat choice UI
    UIHaggling.init(); // Initialize Haggling UI event listeners

    if (DOM.actionForm) { // Core game interactions are available
        UIActionsAndEvents.init();
        UIShopAndInventory.init();
    }

    UIInitialPopups.init();

    // Ensure all full panels are initially hidden after all JS setup
    if (DOM.fullPanelContainers) {
        DOM.fullPanelContainers.forEach(panel => {
            panel.classList.add('hidden');
            // Also ensure their corresponding mini-panels are not marked as expanded
            const miniPanel = document.querySelector(`[aria-controls="${panel.id}"]`);
            if (miniPanel) {
                miniPanel.setAttribute('aria-expanded', 'false');
            }
        });
    }
}


// --- STARTUP ---
document.addEventListener('DOMContentLoaded', main);
