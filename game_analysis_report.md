# Game Analysis Report: GDD vs. Current Implementation

## Introduction
This report details the analysis of the current game codebase and UI/UX against the Game Design Document (GDD). It identifies discrepancies, unimplemented features, and areas for improvement across various aspects of the game.

## 1. User Account and Character Management

**GDD Summary:** Username/Password & Google OAuth, 2 character slots, specific character creation (4d6 drop lowest, 1 reroll), D&D 5e XP/leveling, ASI/Feat choices at milestones, perma-death with viewable graveyard, and slot freeing.

**Analysis & Discrepancies:**

*   **Authentication:**
    *   **Username/Password & Google OAuth:** Generally well-aligned.
    *   **Email in Registration (Minor Discrepancy):** `register.html` includes an email field for username/password accounts, but `app.py` doesn't process/store it. GDD is silent on email for this auth type.
        *   **Recommendation:** Clarify intent. If email is needed (e.g., for recovery), update `app.py` and `users.json` structure. If not, remove from `register.html`.
*   **Character Slots:** Aligned (2 active slots, freed on death).
*   **Initial Character Creation:**
    *   **Name Uniqueness & Stat Rolling/Reroll:** Aligned with GDD.
*   **Progression:**
    *   **XP & Leveling:** XP system and level-up checks are in place.
    *   **HP Increase:** Implemented based on CON and level.
    *   **+1 Skill Bonus on Level-Up (Major Discrepancy):** GDD: "+1 bonus to a chosen skill." Current: `skill_points_to_allocate` are accrued in `Character.py`, but no system exists for players to *choose* a skill and apply this as a direct +1 bonus to its effectiveness.
        *   **Recommendation:** Implement a UI and backend mechanism for players to spend these points on specific skills, and update `Character.get_attribute_score()` to reflect these bonuses.
    *   **ASI/Feat Choice:** Backend logic (`Character.py`) for ASI (+2 one / +1 two stats) and Feat selection at milestone levels is present.
        *   **Gap:** No UI for players to make these choices when `character.pending_asi_feat_choice` is true.
        *   **Recommendation:** Develop UI for ASI/Feat selection at appropriate levels, linking to existing backend methods.
*   **Perma-death & Graveyard:** Aligned with GDD (death by exhaustion, data moved to viewable graveyard, slot freed).

## 2. Shopkeeping Mechanics

**GDD Summary:** Start with a small shop, craft diverse items (potions, scrolls) with quality improving by specific item craft frequency, NPC customer interaction with haggling, shop expansion/specialization.

**Analysis & Discrepancies:**

*   **Starting Shop:** Aligned (player gets a shop).
    *   **Refinement:** GDD's "randomly assigned town" for new characters could be implemented more explicitly.
*   **Crafting:**
    *   **Item Variety & Recipes:** `BASIC_RECIPES` and specialization-based `ADVANCED_RECIPES` exist. Potions are present.
        *   **Gap:** Scroll crafting is mentioned in GDD but no scroll recipes are defined.
        *   **Recommendation:** Add scroll recipes and potentially a "Scribe/Enchanter" specialization if intended.
    *   **Product Quality Progression:** Aligned. `Shop._determine_quality()` uses `crafting_experience[item_name]` and shop level bonus against `QUALITY_THRESHOLDS`. Critical success/failure can modify quality.
    *   **Simple Starting Specializations:** Aligned. Basic recipes are available from the start.
*   **NPC Customer Interaction:**
    *   **Selling to NPCs:** Shop can sell items to generic NPCs (`Shop.complete_sale_to_npc`).
    *   **Haggling (Major Discrepancy):** GDD: "opportunities for haggling." This interactive mechanic is not implemented for player sales to NPCs or purchases from NPCs.
        *   **Recommendation:** Implement an interactive haggling system (likely skill-check based) for transactions with NPCs.
*   **Shop Expansion & Specialization:**
    *   **Expansion (Levels):** Aligned. Shop levels (1-3) affect inventory slots and crafting quality bonus, with upgrade costs. UI exists.
    *   **Specialization:** Aligned. Player can choose specializations ("General Store", "Blacksmith", "Alchemist") with no direct cost, affecting advanced recipe access. UI exists.
    *   **Customer Base Adaptation (Gap):** GDD: Switching specialization might make existing customers "show less interest." This is not currently modeled. NPC buying behavior is generic.
        *   **Recommendation:** Enhance NPC customer simulation to factor in shop specialization history/changes, potentially affecting demand or NPC buy chance for certain item types.

## 3. Economy & Itemization

**GDD Summary:** Gold-based economy, buy/sell items, 3 attunement slots for magical items with persistent effects, consumable items.

**Analysis & Discrepancies:**

*   **Gold-Based Economy:** Aligned. Gold is the central currency.
*   **Buying/Selling:** Aligned. Mechanics for player buying from/selling to their own shop, and player buying from specific NPCs (Hemlock/Borin) are implemented. Prices consider item value, quality, town demand, and shop markups/buybacks. Faction discounts are partially implemented for player buying from their own shop.
*   **Equippable Items & Attunement:**
    *   **Backend:** `Character.py` supports 3 attunement slots, `attune_item()`, `unattune_item()`, and `_apply_item_effects()` for stat/AC bonuses. `Item.py` has `is_magical` and `is_attunement` flags. This is well-aligned.
    *   **UI (Gap):** No UI for players to manage attunement (attune/unattune items).
        *   **Recommendation:** Implement UI in inventory or character screen for attunement management.
*   **Consumable Items:**
    *   **Backend:** `Item.is_consumable` flag and `Character.use_consumable_item()` (with effects like heal_hp, restore_hit_dice) exist.
        *   **Refinement:** `Character.use_consumable_item()` appears to remove the entire item stack. It should decrement quantity and only remove if quantity becomes zero.
        *   **Recommendation:** Update `use_consumable_item()` to correctly handle stacked consumables.
    *   **UI (Gap):** No UI for players to use consumable items from inventory.
        *   **Recommendation:** Add "Use Item" UI functionality for consumables.

## 4. Event System

**GDD Summary:** Dynamic positive/negative random events, possible interruptions, skill check resolution, item rerolls, XP rewards. Base event probability ~5%/hour, modified by behavior, upgrades, town state.

**Analysis & Discrepancies:**

*   **Event Definition & Resolution:** Aligned. `Event` class in `g_event.py` is robust, supporting choices, scaled DCs, skill checks, item interactions (auto-success, DC reduction, item requirement for choice), and varied outcomes with effects (XP, gold, items). `EventManager` handles resolution. `Character.perform_skill_check()` includes "Lucky Charm" reroll.
*   **Event Triggering:** Aligned. `GameManager` triggers events based on `BASE_EVENT_CHANCE_PER_HOUR` (5%) and `SKILL_EVENT_CHANCE_PER_HOUR` (15%) after actions.
*   **Event Probability Modifiers (Gap):** GDD: probability modified by "player behavior, shop upgrades, town state/stability." These modifiers are not currently implemented; probabilities are constant.
    *   **Recommendation:** Implement logic to adjust event probabilities based on these factors.
*   **Action/Rest Interruptions (Refinement/Discrepancy):**
    *   GDD: "events may interrupt player actions or rests...derail the player's current task."
    *   Current (Actions): Events trigger *after* the chosen action's main effects. True interruption/derailment of the action itself doesn't occur.
    *   Current (Long Rests): `Character.attempt_long_rest()` has a generic `interruption_chance`. GDD threats (theft, arson) are not tied to specific events from `g_event.py`.
    *   **Recommendation:**
        *   Clarify design for action interruption. If true derailment is desired, event checks need to precede action effects.
        *   Integrate long rest interruptions with the main event system, using specific events (e.g., "Burglary Attempt") whose likelihood could depend on shop security, etc.
*   **Evolving Story (Gap):** GDD: events "contribute to the evolving story." This is not yet deeply implemented; outcomes are mainly mechanical.
    *   **Recommendation (Future):** Introduce a flagging system or similar for event choices to have persistent narrative consequences.
*   **Item Rerolls (Refinement):** "Lucky Charm" is hardcoded for rerolls.
    *   **Recommendation:** Generalize item-based rerolls (e.g., via an item effect tag).
*   **UI for Events:** Aligned. Event modal (`event-choice-popup`) in `index.html` is populated by `main_ui.js` to display choices and submit decisions.

## 5. Rest Mechanics

**GDD Summary:** Short rests (spend HD to heal), Long rests (full HP/HD recovery, remove exhaustion, needs food/drink, can be interrupted, failure can cause exhaustion). D&D 5e exhaustion effects.

**Analysis & Discrepancies:**

*   **Short Rests:**
    *   **Spending Hit Dice (Discrepancy/Refinement):** GDD: "spend Hit Dice" (plural, implies choice). Current `GameManager` "rest_short" action spends exactly 1 HD. `Character.take_short_rest()` (which might support multiple dice) is unused.
        *   **Recommendation:** Clarify if players should choose HD to spend. If so, update backend and add UI. If not, simplify `Character.take_short_rest()`.
    *   **HD Number & Recovery:** Aligned (HD = level, recovered on long rest as per 5e).
    *   **Consumables Restoring HD:** Aligned (framework exists).
*   **Long Rests:**
    *   **HP/HD Recovery & Exhaustion Removal:** Aligned (full HP, half HD recovered, 1 exhaustion level removed).
    *   **Food/Drink Requirement:** Aligned (generic "Food" & "Drink" items checked and consumed; failure causes exhaustion).
        *   **Refinement:** Consider if specific food/drink items should be used instead of generic ones for more depth.
    *   **Interruptions (Gap):** As per Event System, long rest interruptions are generic and not tied to specific GDD threats or the main event system.
        *   **Recommendation:** Integrate with `g_event.py` system.
    *   **Time Consumption:** Aligned (8 hours).
*   **Exhaustion Mechanics:** Aligned. `EXHAUSTION_EFFECTS` in `Character.py` match GDD/5e (disadvantage on checks, speed reduction, HP max halved, death). Effects on ability checks and speed are implemented.
    *   **Gap (Future):** Disadvantage on Attack Rolls (GDD) needs implementation when combat is added.

## 6. Time System

**GDD Summary:** 24-hour day, one significant action per hour, sleep (8 hours), ~5% event probability per action hour, actions can be interrupted.

**Analysis & Discrepancies:**

*   **24-Hour Cycle & Tracking:** Aligned. `GameTime` class handles this well.
*   **Action Per Hour & Time Advancement:** Aligned. `GameManager.perform_hourly_action()` advances time by 1 hour for most actions, or more for specific ones (travel, long rest).
*   **Sleep:** Aligned (Long rest action takes 8 hours).
*   **Event Probability per Hour:** Aligned (base 5% chance implemented in `GameManager`). Modifiers are a separate point (see Event System).
*   **Action Interruption (Discrepancy/Refinement):** GDD: "action may be interrupted...derail the task." Current: Events resolve *after* action's primary effects.
    *   **Recommendation:** Clarify "derail." If true interruption is meant, event checks in `GameManager` must precede action effects, which is a complex change.

## 7. World Interaction (Towns & Factions)

**GDD Summary - Towns:** Unique properties (resources, NPCs, local events), influence on crafting/market/pricing, local recipes.
**GDD Summary - Factions:** Joinable, reputation/ranks, benefits (discounts, exclusive items/quests), HQs in towns.

**Analysis & Discrepancies - Towns:**

*   **Town Definition & Properties:** Aligned. `Town` class supports properties, resources, NPCs, market modifiers, sub-locations, faction HQs. Sample towns exist.
*   **Nearby Resources & NPC Crafters:** Aligned. Resources affect gathering. NPCs (Hemlock, Borin) offer some services/items.
    *   **Gap:** NPC "training," "rare components," and NPC-driven quests are not implemented.
    *   **Recommendation:** Expand NPC crafter interactions to include training, rare component sales, and a basic quest system.
*   **Recurring Local Events (Major Gap):** GDD's concept of scheduled or multi-day random town-specific events (festivals, etc.) affecting the town's economy or resource availability is not implemented.
    *   **Recommendation:** Develop a system to manage and trigger these town-specific local events, with defined durations and effects.
*   **Market Demands & Pricing:** Aligned. `Town.market_demand_modifiers` affect `Shop.calculate_sale_price()`.
*   **Local Crafting Recipes (Gap):** Recipes are currently global. GDD suggests town-specific recipes.
    *   **Recommendation:** Allow towns to define local recipes; characters could learn them via interaction or discovery.

**Analysis & Discrepancies - Factions:**

*   **Faction Definition & Character Data:** Aligned. `factions.py` defines factions, ranks, benefits, join requirements. `Character.py` stores faction reputation/rank.
*   **Joining & Reputation/Ranks:** Aligned. `Character.join_faction()` (with requirement checks) and `update_faction_reputation()` are implemented. Joining via HQs in towns is checked.
*   **Faction Benefits:**
    *   `shop_discount` (Merchant's Guild): Implemented in `Shop.calculate_sale_price()`.
    *   **Gap:** Other benefits (`access_exclusive_wares`, NPC `dialogue_options`, `reduced_crime_chance`) are defined but not mechanically active.
    *   **Recommendation:** Implement game mechanics to check for and apply these other benefit types.
*   **UI for Factions (Implied Gap):** No dedicated UI to view faction status, join factions, or see benefits/requirements clearly.
    *   **Recommendation:** Create a Faction UI panel.
*   **Extensibility:** Aligned. System is data-driven and appears extensible.

## 8. UI/UX Specifics (from `main_game_interface_review.md`)

*   **Overall Layout:**
    *   Potential for clutter with current panel system, especially if map becomes interactive.
    *   Button styling needs more consistency (base class + modifiers).
    *   Accessibility: ARIA attributes largely missing for custom components.
*   **Navigation:**
    *   Side hover-panels: Consider click-to-toggle for better UX.
    *   Map: Currently a placeholder; future interactive map needs careful design regarding GDD features and potential UI issues (loading, readability, controls).
    *   Sub-location navigation via buttons is functional.
*   **Basic Actions:**
    *   Interaction prompts (button labels) are clear.
    *   Feedback (toasts, journal) is present.
    *   Controls are standard web; JS structure is a long-term risk to responsiveness.

## 9. Code Structure and Quality (from `ui_code_analysis.md`)

*   **JavaScript (`main_ui.js`):**
    *   **Major Issue:** Monolithic `DOMContentLoaded` handler, global variables, complex conditionals.
        *   **Recommendation (High Priority):** Refactor into modules/focused functions. Use `let/const`. Define constants for magic strings.
*   **HTML (`index.html`):**
    *   Good Jinja use.
    *   **Issues:** Inline styles, overuse of `div`s, missing ARIA.
        *   **Recommendation:** Move styles to CSS. Use semantic tags. Implement ARIA.
*   **CSS (`style.css`):**
    *   Good use of CSS variables, Flexbox.
    *   **Issues:** Specificity/`!important`, potential layout fragility (absolute positioning), organization, magic numbers, inconsistent button styling.
        *   **Recommendation:** Reduce specificity, improve button styling consistency, organize better.
     
*   **Update (2025-06-24 11:50am): UI Refactoring and Panel Bug Fix**
    *   Significant refactoring of frontend code (`main_ui.js`, `index.html`, `style.css`) was completed to address several points from the `ui_code_analysis.md`.
    *   **`main_ui.js`**: The monolithic `DOMContentLoaded` listener was broken down into smaller, more manageable modules/objects (e.g., `UIPanels`, `UIBottomTabs`, `UIActionsAndEvents`). DOM elements are now cached in a global `DOM` object for efficiency. Magic strings for action names were replaced with constants. `var` declarations were updated to `let` and `const`.
    *   **`index.html`**: All inline `style` attributes were removed and replaced with CSS classes (primarily a utility `.hidden` class). Semantic HTML tags such as `<main>`, `<aside>`, `<nav>`, and `<section>` were introduced to improve document structure. ARIA attributes (e.g., `role`, `aria-controls`, `aria-expanded`, `aria-modal`, `aria-labelledby`) were added or enhanced for better accessibility of custom components like modals and tab panels. Commented-out code and a duplicate heading were removed.
    *   **`style.css`**: The stylesheet was reorganized with more descriptive comments. The `!important` directive in `.active-tab-button` was removed. A CSS variable (`--spacing-unit`) was introduced to standardize spacing. Default visibility for JavaScript-toggled UI elements (like full panels and dynamic forms) is now more robustly handled through CSS classes.
    *   **Bug Fix**: Addressed an issue where all full-panel module windows (inventory, shop management, etc.) were incorrectly appearing simultaneously after game actions. The JavaScript logic controlling panel visibility (`UIPanels.init` and a safeguard in `main()`) was corrected to ensure panels are hidden by default on page load and only the specifically activated panel is shown.


## Overall Conclusion & Prioritized Recommendations

The game has a solid foundational implementation for many core GDD features. Key areas requiring attention are:

**High Priority (Gameplay Impact & Foundational):**

1.  **Implement "+1 Skill Bonus Choice":** Crucial for character progression as per GDD.
2.  **Implement UI for ASI/Feat Choice:** Essential for milestone level progression.
3.  **Implement Interactive NPC Haggling:** A core GDD shopkeeping interaction.
4.  **Integrate Long Rest Interruptions with Event System:** Make interruptions more thematic and dynamic.
5.  **Implement UI for Attunement & Consumable Use:** Core item interactions are missing UI.

**Medium Priority (Enhance Core Loops & Address Gaps):**

1.  **Recurring Local Town Events:** Adds significant world dynamism.
2.  **Refine Action Interruption by Events:** Clarify design and adjust event timing if needed.
3.  **Implement More Faction Benefits & Faction UI:** Make factions more impactful and visible.
4.  **Town-Specific Crafting Recipes:** Adds to world flavor and strategic crafting.
5.  **Handle Consumable Item Quantities Correctly:** Fix `use_consumable_item` logic.
6.  **Address Event Probability Modifiers:** Make event system more dynamic.

**Code Quality & UI/UX (Ongoing / Foundational for Future Development):**

1.  **JavaScript Refactoring (`main_ui.js`):** Address monolithic structure for maintainability.
2.  **HTML Semantics & ARIA:** Improve accessibility and structure.
3.  **CSS Consistency & Robustness:** Refine styling for buttons, review layout fragility.
4.  **Clarify Email in Registration:** Minor data handling consistency.
5.  **Add Scroll Crafting:** If intended as a core crafting type.

Addressing these points will bring the game closer to the GDD's vision and improve the overall player experience and codebase health.
