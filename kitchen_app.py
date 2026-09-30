import streamlit as st
from supabase import create_client


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="My Kitchen",
    page_icon="🥫",
    layout="centered"
)


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def get_supabase():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


supabase = get_supabase()


# ============================================================
# SESSION STATE
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "pending_item" not in st.session_state:
    st.session_state.pending_item = None

if "show_shopping_popup" not in st.session_state:
    st.session_state.show_shopping_popup = False


# ============================================================
# AUTHENTICATION
# ============================================================

def login_page():

    st.title("🏠 My Kitchen")

    st.write(
        "Your personal kitchen inventory."
    )

    login_tab, signup_tab = st.tabs(
        [
            "Log in",
            "Create account"
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Log in",
            use_container_width=True
        ):

            try:

                response = (
                    supabase
                    .auth
                    .sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                )

                st.session_state.user = response.user

                st.success(
                    "Logged in!"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Login failed: {e}"
                )

    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    with signup_tab:

        new_email = st.text_input(
            "Email",
            key="signup_email"
        )

        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        if st.button(
            "Create account",
            use_container_width=True
        ):

            try:

                response = (
                    supabase
                    .auth
                    .sign_up({
                        "email": new_email,
                        "password": new_password
                    })
                )

                if response.user:

                    st.success(
                        "Account created! "
                        "Check your email if confirmation is required."
                    )

                else:

                    st.error(
                        "Supabase did not create the account."
                    )

            except Exception as e:

                st.error(
                    f"Could not create the account: {e}"
                )


# ============================================================
# INVENTORY FUNCTIONS
# ============================================================

def get_items(user_id):

    response = (
        supabase
        .table("inventory")
        .select("*")
        .eq("user_id", user_id)
        .order("id")
        .execute()
    )

    return response.data


def add_item(
    user_id,
    name,
    location
):

    (
        supabase
        .table("inventory")
        .insert({
            "user_id": user_id,
            "name": name,
            "location": location,
            "available": True
        })
        .execute()
    )


def update_item(
    item_id,
    user_id,
    available
):

    (
        supabase
        .table("inventory")
        .update({
            "available": available
        })
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )


def delete_item(
    item_id,
    user_id
):

    (
        supabase
        .table("inventory")
        .delete()
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )


# ============================================================
# SHOPPING LIST FUNCTIONS
# ============================================================

def get_shopping_items(user_id):

    response = (
        supabase
        .table("shopping_list")
        .select("*")
        .eq("user_id", user_id)
        .order("id")
        .execute()
    )

    return response.data


def add_to_shopping_list(
    user_id,
    name,
    inventory_id
):

    # --------------------------------------------------------
    # Don't create a duplicate unfinished shopping item
    # --------------------------------------------------------

    existing = (
        supabase
        .table("shopping_list")
        .select("id")
        .eq("user_id", user_id)
        .eq("inventory_id", inventory_id)
        .eq("completed", False)
        .execute()
    )

    if existing.data:

        return


    # --------------------------------------------------------
    # Add item
    # --------------------------------------------------------

    (
        supabase
        .table("shopping_list")
        .insert({
            "user_id": user_id,
            "name": name,
            "inventory_id": inventory_id,
            "completed": False
        })
        .execute()
    )


def update_shopping_item(
    item_id,
    user_id,
    completed
):

    (
        supabase
        .table("shopping_list")
        .update({
            "completed": completed
        })
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )


def delete_shopping_item(
    item_id,
    user_id
):

    (
        supabase
        .table("shopping_list")
        .delete()
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )


def clear_completed_items(user_id):

    (
        supabase
        .table("shopping_list")
        .delete()
        .eq("user_id", user_id)
        .eq("completed", True)
        .execute()
    )


# ============================================================
# KITCHEN PAGE
# ============================================================

def kitchen_page(user):

    user_id = user.id

    st.title("🥫 My Kitchen")

    st.caption(
        "Check an item when you have it. "
        "Uncheck it when you run out."
    )

    items = get_items(user_id)


    # ========================================================
    # ADD ITEM
    # ========================================================

    with st.expander("➕ Add an item"):

        item_name = st.text_input(
            "Item name",
            placeholder="e.g. Milk",
            key="new_item_name"
        )

        location = st.selectbox(
            "Where is it?",
            [
                "Fridge",
                "Cupboard",
                "Freezer"
            ],
            key="new_item_location"
        )

        if st.button(
            "Add item",
            use_container_width=True
        ):

            if item_name.strip():

                add_item(
                    user_id,
                    item_name.strip(),
                    location
                )

                st.success(
                    f"Added {item_name.strip()}!"
                )

                st.rerun()

            else:

                st.warning(
                    "Please enter an item name."
                )


    st.divider()


    # ========================================================
    # LOCATION SECTIONS
    # ========================================================

    locations = [
        ("Fridge", "🧊 Fridge"),
        ("Cupboard", "🗄️ Cupboard"),
        ("Freezer", "❄️ Freezer")
    ]


    for location, display_name in locations:

        st.subheader(display_name)


        location_items = [
            item
            for item in items
            if item["location"] == location
        ]


        if not location_items:

            st.caption(
                "Nothing here yet."
            )

            continue


        for item in location_items:

            col1, col2 = st.columns(
                [6, 1]
            )


            # =================================================
            # CHECKBOX
            # =================================================

            with col1:

                checked = st.checkbox(
                    item["name"],
                    value=item["available"],
                    key=f"inventory_{item['id']}"
                )


                # ---------------------------------------------
                # SOMETHING CHANGED
                # ---------------------------------------------

                if checked != item["available"]:


                    # =========================================
                    # ITEM BECAME UNAVAILABLE
                    # =========================================

                    if not checked:

                        # Update inventory first
                        update_item(
                            item["id"],
                            user_id,
                            False
                        )

                        # Remember which item triggered this
                        st.session_state.pending_item = item

                        st.session_state.show_shopping_popup = True

                        st.rerun()


                    # =========================================
                    # ITEM BECAME AVAILABLE
                    # =========================================

                    else:

                        update_item(
                            item["id"],
                            user_id,
                            True
                        )

                        st.rerun()


            # =================================================
            # DELETE BUTTON
            # =================================================

            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_{item['id']}"
                ):

                    delete_item(
                        item["id"],
                        user_id
                    )

                    st.rerun()


# ============================================================
# SHOPPING POPUP
# ============================================================

def shopping_popup(user):

    if not st.session_state.show_shopping_popup:

        return


    item = st.session_state.pending_item


    if not item:

        return


    st.divider()


    st.warning(
        f"🛒 You're out of **{item['name']}**."
    )


    st.write(
        "Would you like to add it to your shopping list?"
    )


    col1, col2 = st.columns(2)


    # ========================================================
    # ADD
    # ========================================================

    with col1:

        if st.button(
            "🛒 Add to shopping list",
            use_container_width=True
        ):

            add_to_shopping_list(
                user.id,
                item["name"],
                item["id"]
            )

            st.session_state.show_shopping_popup = False

            st.session_state.pending_item = None

            st.success(
                f"Added {item['name']} "
                "to your shopping list!"
            )

            st.rerun()


    # ========================================================
    # DON'T ADD
    # ========================================================

    with col2:

        if st.button(
            "No thanks",
            use_container_width=True
        ):

            st.session_state.show_shopping_popup = False

            st.session_state.pending_item = None

            st.rerun()


# ============================================================
# SHOPPING LIST PAGE
# ============================================================

def shopping_list_page(user):

    user_id = user.id

    st.title("🛒 Shopping List")

    st.caption(
        "Things you need to buy."
    )

    items = get_shopping_items(user_id)

    # ========================================================
    # EMPTY LIST
    # ========================================================

    if not items:

        st.info(
            "Your shopping list is empty! 🎉"
        )

        return

    # ========================================================
    # SPLIT INTO INCOMPLETE / COMPLETE
    # ========================================================

    incomplete = [
        item
        for item in items
        if not item["completed"]
    ]

    completed = [
        item
        for item in items
        if item["completed"]
    ]

    # ========================================================
    # TO BUY
    # ========================================================

    if incomplete:

        st.subheader(
            f"To buy ({len(incomplete)})"
        )

        for item in incomplete:

            col1, col2 = st.columns([6, 1])

            with col1:

                checked = st.checkbox(
                    item["name"],
                    value=False,
                    key=f"shopping_{item['id']}"
                )

                if checked:

                    # ------------------------------------------------
                    # Mark shopping item as completed
                    # ------------------------------------------------

                    update_shopping_item(
                        item["id"],
                        user_id,
                        True
                    )

                    # ------------------------------------------------
                    # Restore the exact kitchen item
                    # ------------------------------------------------

                    inventory_id = item.get("inventory_id")

                    if inventory_id is not None:

                        update_item(
                            inventory_id,
                            user_id,
                            True
                        )

                        # ------------------------------------------------
                        # IMPORTANT:
                        # Reset Streamlit's remembered checkbox state
                        # ------------------------------------------------

                        inventory_key = f"inventory_{inventory_id}"

                        if inventory_key in st.session_state:
                            del st.session_state[inventory_key]

                    # ------------------------------------------------
                    # Refresh the app
                    # ------------------------------------------------

                    st.rerun()

            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_shopping_{item['id']}"
                ):

                    delete_shopping_item(
                        item["id"],
                        user_id
                    )

                    st.rerun()

    # ========================================================
    # COMPLETED
    # ========================================================

    if completed:

        st.divider()

        st.subheader("Completed")

        for item in completed:

            col1, col2 = st.columns([6, 1])

            with col1:

                st.checkbox(
                    item["name"],
                    value=True,
                    disabled=True,
                    key=f"completed_{item['id']}"
                )

            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_completed_{item['id']}"
                ):

                    delete_shopping_item(
                        item["id"],
                        user_id
                    )

                    st.rerun()

        # ----------------------------------------------------
        # CLEAR COMPLETED
        # ----------------------------------------------------

        st.divider()

        if st.button(
            "🧹 Clear completed",
            use_container_width=True
        ):

            clear_completed_items(user_id)

            st.rerun()


    # ========================================================
    # COMPLETED
    # ========================================================

    if completed:

        st.divider()

        st.subheader(
            "Completed"
        )


        for item in completed:

            col1, col2 = st.columns(
                [6, 1]
            )


            with col1:

                st.checkbox(
                    item["name"],
                    value=True,
                    disabled=True,
                    key=f"completed_{item['id']}"
                )


            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_completed_{item['id']}"
                ):

                    delete_shopping_item(
                        item["id"],
                        user_id
                    )

                    st.rerun()


        # ----------------------------------------------------
        # CLEAR COMPLETED
        # ----------------------------------------------------

        st.divider()

        if st.button(
            "🧹 Clear completed",
            use_container_width=True
        ):

            clear_completed_items(
                user_id
            )

            st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

def kitchen_app():

    user = st.session_state.user


    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.write(
            f"👤 {user.email}"
        )

        st.divider()


        if st.button(
            "Log out",
            use_container_width=True
        ):

            supabase.auth.sign_out()

            st.session_state.user = None

            st.rerun()


    # ========================================================
    # TABS
    # ========================================================

    kitchen_tab, shopping_tab = st.tabs(
        [
            "🥫 Kitchen",
            "🛒 Shopping List"
        ]
    )


    # ========================================================
    # KITCHEN TAB
    # ========================================================

    with kitchen_tab:

        kitchen_page(user)

        shopping_popup(user)


    # ========================================================
    # SHOPPING TAB
    # ========================================================

    with shopping_tab:

        shopping_list_page(user)


# ============================================================
# APP ENTRY POINT
# ============================================================

if st.session_state.user is None:

    login_page()

else:

    kitchen_app()
