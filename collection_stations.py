
import streamlit as st
import re
import qrcode
from io import BytesIO

# =========================================================
# ECOLOOP NODE — GLOBAL SMART COLLECTION STATIONS
# =========================================================

TABLE = "collection_stations"

COUNTRIES = {
    "Zimbabwe": "ZW",
    "South Africa": "ZA",
    "Botswana": "BW",
    "Zambia": "ZM",
    "Kenya": "KE",
    "Nigeria": "NG",
    "Ghana": "GH",
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Australia": "AU",
    "Other": "XX"
}

MATERIALS = [
    "Plastic",
    "Paper",
    "Metal",
    "Glass",
    "Organic",
    "Electronic",
    "Textiles",
    "Other"
]

STATION_TYPES = [
    "EcoLoop-owned",
    "Partner station",
    "Community collection point"
]


# =========================================================
# QR CODE GENERATION
# =========================================================

def generate_qr_code(station_code):
    """Generate a downloadable QR code for a station."""

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )

        # The QR identifies the station.
        # It does not authorise or verify a contribution.
        qr.add_data(f"ECOLOOP-STATION:{station_code}")
        qr.make(fit=True)

        image = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        buffer = BytesIO()
        image.save(buffer, format="PNG")

        return buffer.getvalue()

    except Exception as e:
        st.error(f"QR generation failed: {e}")
        return None



# =========================================================
# STATION DATABASE FUNCTIONS
# =========================================================

def get_stations(supabase, active_only=False):
    """Retrieve collection stations."""

    try:
        query = (
            supabase.table(TABLE)
            .select("*")
        )

        if active_only:
            query = query.eq("is_active", True)

        response = query.order(
            "created_at",
            desc=True
        ).execute()

        return response.data or [], None

    except Exception as e:
        st.error(f"Station database error: {e}")
        return [], str(e)



def generate_station_prefix(country_code, city):
    """Generate the station code prefix."""

    city_code = re.sub(
        r"[^A-Z]",
        "",
        city.upper()
    )[:3]

    if not city_code:
        city_code = "GEN"

    return f"ECO-{country_code}-{city_code}"


def create_station(
    supabase,
    station_name,
    country,
    region,
    city,
    address,
    capacity_kg,
    accepted_materials,
    station_type,
    latitude=None,
    longitude=None
):
    """Register a new official EcoLoop station."""

    try:
        country_code = COUNTRIES.get(country, "XX")

        prefix = generate_station_prefix(
            country_code,
            city
        )

        existing = (
            supabase.table(TABLE)
            .select("station_code")
            .like("station_code", f"{prefix}-%")
            .execute()
        )

        existing_numbers = []

        for station in existing.data or []:
            code = station.get("station_code", "")

            try:
                existing_numbers.append(
                    int(code.split("-")[-1])
                )
            except (ValueError, IndexError):
                continue

        next_number = max(
            existing_numbers,
            default=0
        ) + 1

        station_code = (
            f"{prefix}-{next_number:04d}"
        )

        station_data = {
            "station_code": station_code,
            "station_name": station_name.strip(),
            "country": country,
            "country_code": country_code,
            "region": region.strip(),
            "city": city.strip(),
            "address": address.strip(),
            "capacity_kg": float(capacity_kg),
            "accepted_materials": accepted_materials,
            "station_type": station_type,
            "is_active": True,

            # QR identification
            "qr_code": station_code,
            "qr_enabled": True,

            # Future hardware integration
            "sensor_enabled": False,
            "sensor_status": "not_installed",
            "fill_level": 0
        }

        if latitude is not None:
            station_data["latitude"] = float(latitude)

        if longitude is not None:
            station_data["longitude"] = float(longitude)

        supabase.table(TABLE).insert(
            station_data
        ).execute()

        return True, station_code

    except Exception as e:
        return False, str(e)


def update_station_status(
    supabase,
    station_id,
    is_active
):
    """Activate or deactivate a station."""

    try:
        supabase.table(TABLE).update({
            "is_active": bool(is_active)
        }).eq("id", station_id).execute()

        return True, "Station status updated."

    except Exception as e:
        return False, str(e)


# =========================================================
# STATION DISPLAY
# =========================================================

def render_station_card(
    station,
    is_admin
):
    """Display one station and its QR code."""

    station_id = station.get("id")
    station_code = station.get("station_code", "")
    active = station.get("is_active", False)

    with st.container(border=True):

        left, right = st.columns([3, 1])

        with left:

            st.subheader(
                station.get(
                    "station_name",
                    "Unnamed Station"
                )
            )

            st.code(station_code)

            st.write(
                f"**Location:** "
                f"{station.get('city', '')}, "
                f"{station.get('region', '')}, "
                f"{station.get('country', '')}"
            )

            st.write(
                f"**Address:** "
                f"{station.get('address', 'Not provided')}"
            )

            st.write(
                f"**Station Type:** "
                f"{station.get('station_type', 'Not specified')}"
            )

            st.write(
                f"**Capacity:** "
                f"{station.get('capacity_kg', 0)} kg"
            )

            materials = station.get(
                "accepted_materials",
                []
            ) or []

            st.write(
                "**Accepted Materials:** "
                + ", ".join(materials)
            )

        with right:

            if active:
                st.success("Active")
            else:
                st.warning("Inactive")

            sensor_status = station.get(
                "sensor_status",
                "not_installed"
            )

            if sensor_status == "connected":
                st.success("Sensor connected")
            elif sensor_status == "offline":
                st.warning("Sensor offline")
            else:
                st.info("Sensor not installed")

        # QR CODE
        st.divider()

        qr_enabled = station.get(
            "qr_enabled",
            False
        )

        if qr_enabled and station_code:

            with st.expander(
                "View Station QR Code"
            ):

                qr_image = generate_qr_code(
                    station_code
                )

                if qr_image:

                    st.image(
                        qr_image,
                        caption=f"Scan to identify {station_code}",
                        width=220
                    )

                    st.download_button(
                        label="Download Station QR Code",
                        data=qr_image,
                        file_name=f"{station_code}_QR.png",
                        mime="image/png",
                        key=f"download_qr_{station_id}"
                    )

        if is_admin:

            if st.button(
                "Deactivate Station" if active else "Activate Station",
                key=f"toggle_station_{station_id}",
                use_container_width=True
            ):

                return station_id, not active

    return None


# =========================================================
# MAIN COLLECTION STATIONS PAGE
# =========================================================

def render_collection_stations(
    supabase,
    user_role=None
):
    """Main EcoLoop collection stations page."""

    st.title("Collection Stations")

    st.caption(
        "Discover and manage EcoLoop collection points worldwide."
    )

    is_admin = user_role in [
        "admin",
        "super_admin"
    ]

    if st.button(
        "Refresh Stations",
        key="refresh_global_stations"
    ):
        st.rerun()

    stations, error = get_stations(supabase)

    if error:

        st.error(
            "Could not load collection stations."
        )

        st.caption(error)

        return

    active_stations = [
        s for s in stations
        if s.get("is_active") is True
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Stations",
        len(stations)
    )

    col2.metric(
        "Active Stations",
        len(active_stations)
    )

    col3.metric(
        "Inactive Stations",
        len(stations) - len(active_stations)
    )

    st.divider()

    # -----------------------------------------------------
    # REGISTER NEW STATION
    # -----------------------------------------------------

    if is_admin:

        st.subheader("Register New Station")

        with st.expander(
            "Create Collection Station"
        ):

            with st.form("global_collection_station_form"):

                station_name = st.text_input(
                    "Station Name",
                    placeholder="Community Recycling Centre"
                )

                station_type = st.selectbox(
                    "Station Type",
                    STATION_TYPES
                )

                country = st.selectbox(
                    "Country",
                    list(COUNTRIES.keys())
                )

                region = st.text_input(
                    "State / Province / Region"
                )

                city = st.text_input(
                    "City"
                )

                address = st.text_area(
                    "Physical Address"
                )

                capacity = st.number_input(
                    "Maximum Capacity (kg)",
                    min_value=1.0,
                    value=500.0,
                    step=50.0
                )

                accepted_materials = st.multiselect(
                    "Accepted Materials",
                    MATERIALS
                )

                st.markdown(
                    "**Optional GPS Coordinates**"
                )

                add_coordinates = st.checkbox(
                    "Add GPS coordinates"
                )

                latitude = None
                longitude = None

                if add_coordinates:

                    latitude = st.number_input(
                        "Latitude",
                        min_value=-90.0,
                        max_value=90.0,
                        value=0.0,
                        format="%.6f"
                    )

                    longitude = st.number_input(
                        "Longitude",
                        min_value=-180.0,
                        max_value=180.0,
                        value=0.0,
                        format="%.6f"
                    )

                submitted = st.form_submit_button(
                    "Register Station",
                    use_container_width=True
                )

                if submitted:

                    if not station_name.strip():
                        st.error("Enter a station name.")

                    elif not city.strip():
                        st.error("Enter the city.")

                    elif not region.strip():
                        st.error("Enter the region or province.")

                    elif not address.strip():
                        st.error("Enter the physical address.")

                    elif not accepted_materials:
                        st.error(
                            "Select at least one accepted material."
                        )

                    elif add_coordinates and (
                        latitude == 0.0 and longitude == 0.0
                    ):
                        st.error(
                            "Enter valid coordinates or leave GPS disabled."
                        )

                    else:

                        success, result = create_station(
                            supabase=supabase,
                            station_name=station_name,
                            country=country,
                            region=region,
                            city=city,
                            address=address,
                            capacity_kg=capacity,
                            accepted_materials=accepted_materials,
                            station_type=station_type,
                            latitude=latitude,
                            longitude=longitude
                        )

                        if success:

                            st.success(
                                f"Station registered successfully: {result}"
                            )

                            st.rerun()

                        else:

                            st.error(
                                f"Station registration failed: {result}"
                            )

    # -----------------------------------------------------
    # SEARCH AND FILTER
    # -----------------------------------------------------

    st.divider()

    st.subheader("Registered Stations")

    search = st.text_input(
        "Search by station, city or country",
        placeholder="Search stations..."
    )

    status_filter = st.selectbox(
        "Filter Stations",
        [
            "All Stations",
            "Active Only",
            "Inactive Only"
        ]
    )

    filtered = []

    for station in stations:

        active = station.get("is_active", False)

        if status_filter == "Active Only" and not active:
            continue

        if status_filter == "Inactive Only" and active:
            continue

        searchable = " ".join([
            str(station.get("station_name", "")),
            str(station.get("station_code", "")),
            str(station.get("country", "")),
            str(station.get("city", "")),
            str(station.get("region", ""))
        ]).lower()

        if search.lower() not in searchable:
            continue

        filtered.append(station)

    if not filtered:

        st.info(
            "No matching collection stations found."
        )

    # -----------------------------------------------------
    # DISPLAY STATIONS
    # -----------------------------------------------------

    for station in filtered:

        action = render_station_card(
            station,
            is_admin
        )

        if action:

            station_id, new_status = action

            success, message = update_station_status(
                supabase,
                station_id,
                new_status
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.divider()

    st.caption(
        "EcoLoop Node | Powered by Next Gen Impact Hub (NGIH)"
    )
