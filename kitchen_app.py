import streamlit as st
from supabase import create_client


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="My Kitchen",
    page_icon="🥫",
    layout="centered"
)


# ==================================================
# SUPABASE CONNECTION
# ==================================================

@st.cache_resource
def get_supabase():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


supabase = get_supabase()


# ==================================================
# SESSION STATE
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None


# ==================================================
# LOGIN / SIGNUP PAGE
# ==================================================

def login_page():

    st.title("🏠 My Kitchen")
    st.caption("Your kitchen, wherever you are.")

    tab_login, tab_signup = st.tabs([
        "Log in",
        "Create account"
    ])


    # ----------------------------------------------
    # LOGIN
    # ----------------------------------------------

    with tab_login:

        st.subheader("Welcome back!")

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

                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state.user = response.user

                st.success("Logged in!")

                st.rerun()

            except Exception as e:

                st.error(f"Login failed: {e}")


    # ----------------------------------------------
    # SIGN UP
    # ----------------------------------------------

    with tab_signup:

        st.subheader("Create your kitchen")

        new_email = st.text_input(
            "Email",
            key="signup_email"
        )

        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password"
        )


        if st.button(
            "Create account",
            use_container_width=True
        ):

            if new_password != confirm_password:

                st.error("The passwords don't match.")

            elif len(new_password) < 6:

                st.error(
                    "Your password must be at least 6 characters."
                )

            else:

                try:

                    response = supabase.auth.sign_up({
                        "email": new_email,
                        "password": new_password
                    })

                    st.success(
                        "Account created! "
                        "Check your email if confirmation is required."
                    )

                except Exception as e:

                     st.error(f"Could not create the account: {e}")


# ==================================================
# DATABASE FUNCTIONS
# ==================================================

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


def add_item(user_id, name, location):

    supabase.table("inventory").insert({
        "user_id": user_id,
        "name": name,
        "location": location,
        "available": True
    }).execute()


def update_item(item_id, user_id, available):

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


def delete_item(item_id, user_id):

    (
        supabase
        .table("inventory")
        .delete()
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )


# ==================================================
# MAIN KITCHEN APP
# ==================================================

def kitchen_app():

    user = st.session_state.user
    user_id = user.id


    # ----------------------------------------------
    # HEADER
    # ----------------------------------------------

    col1, col2 = st.columns([4, 1])

    with col1:

        st.title("🏠 My Kitchen")

        st.caption(
            "Keep track of what's actually in your kitchen."
        )

    with col2:

        if st.button("Log out"):

            supabase.auth.sign_out()

            st.session_state.user = None

            st.rerun()


    st.divider()


    # ----------------------------------------------
    # ADD ITEM
    # ----------------------------------------------

    st.subheader("➕ Add something")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:

        new_item = st.text_input(
            "Item",
            placeholder="e.g. Milk",
            label_visibility="collapsed"
        )

    with col2:

        location = st.selectbox(
            "Location",
            [
                "Fridge",
                "Cupboard",
                "Freezer"
            ],
            label_visibility="collapsed"
        )

    with col3:

        add_button = st.button(
            "Add",
            use_container_width=True
        )


    if add_button:

        if new_item.strip():

            add_item(
                user_id,
                new_item.strip(),
                location
            )

            st.success(
                f"Added {new_item.strip()}!"
            )

            st.rerun()

        else:

            st.warning(
                "Enter an item first!"
            )


    st.divider()


    # ----------------------------------------------
    # GET INVENTORY
    # ----------------------------------------------

    items = get_items(user_id)


    icons = {
        "Fridge": "🧊",
        "Cupboard": "🥫",
        "Freezer": "❄️"
    }


    locations = [
        "Fridge",
        "Cupboard",
        "Freezer"
    ]


    # ----------------------------------------------
    # DISPLAY INVENTORY
    # ----------------------------------------------

    for current_location in locations:

        st.subheader(
            f"{icons[current_location]} "
            f"{current_location}"
        )


        location_items = [
            item
            for item in items
            if item["location"] == current_location
        ]


        if not location_items:

            st.caption(
                "Nothing here yet."
            )


        for item in location_items:

            item_id = item["id"]

            name = item["name"]

            available = item["available"]


            col1, col2 = st.columns([5, 1])


            with col1:

                checked = st.checkbox(
                    name,
                    value=available,
                    key=f"item_{item_id}"
                )


                if checked != available:

                    update_item(
                        item_id,
                        user_id,
                        checked
                    )

                    st.rerun()


            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_{item_id}"
                ):

                    delete_item(
                        item_id,
                        user_id
                    )

                    st.rerun()


        st.write("")


    # ----------------------------------------------
    # AI BUTTON
    # ----------------------------------------------

    st.divider()

    st.subheader("✨ Hungry?")


    if st.button(
        "✨ What can I make?",
        use_container_width=True
    ):

        available_items = [
            item["name"]
            for item in items
            if item["available"]
        ]


        if available_items:

            st.info(
                "AI recipe suggestions will go here!\n\n"
                "**Currently available:** "
                + ", ".join(available_items)
            )

        else:

            st.warning(
                "Your kitchen appears to be completely empty. "
                "Time to go shopping 😭"
            )


    # ----------------------------------------------
    # FOOTER
    # ----------------------------------------------

    st.divider()


    available_count = sum(
        1
        for item in items
        if item["available"]
    )


    st.caption(
        f"{available_count} items currently in stock · "
        f"{len(items)} items tracked"
    )


# ==================================================
# APP ENTRY POINT
# ==================================================

if st.session_state.user is None:

    login_page()

else:

    kitchen_app()
