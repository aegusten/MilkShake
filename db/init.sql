/***********************************************************************
 * MilkShake – core schema
 * Postgres 15+   (uuid-ossp + enum + constraints)
 **********************************************************************/
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

/*--------------------------------------------------
  ENUM: drink_type  (easy to extend later)
--------------------------------------------------*/
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'drink_type') THEN
        CREATE TYPE drink_type AS ENUM ('soft', 'milkshake', 'cocktail', 'other');
    END IF;
END $$;

/***********************************************************************
 * 1.  Administrative users
 *    (1-2 admins only, but still nice to persist)
 **********************************************************************/
CREATE TABLE admins (
    id            UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    email         TEXT            NOT NULL UNIQUE,
    password_hash TEXT            NOT NULL,                 -- bcrypt/argon2
    is_active     BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP       NOT NULL DEFAULT NOW()
);

/***********************************************************************
 * 2.  Drink categories  (sortable)
 **********************************************************************/
CREATE TABLE drink_categories (
    id          UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    name        TEXT            NOT NULL UNIQUE,
    sort_order  INT             NOT NULL DEFAULT 0,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drink_categories_sort ON drink_categories(sort_order);

/***********************************************************************
 * 3.  Drinks
 **********************************************************************/
CREATE TABLE drinks (
    id           UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    name         TEXT            NOT NULL,
    description  TEXT,
    price        NUMERIC(10,2)   NOT NULL CHECK (price >= 0),
    type         drink_type      NOT NULL DEFAULT 'other',
    image_cover  TEXT,                           -- first image shortcut
    category_id  UUID            NOT NULL
                 REFERENCES drink_categories(id) ON DELETE CASCADE,
    created_at   TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drinks_category          ON drinks(category_id);
CREATE INDEX idx_drinks_type              ON drinks(type);

/***********************************************************************
 * 4.  Drink images  (≤ 3 per drink, position 1-3)
 **********************************************************************/
CREATE TABLE drink_images (
    id         UUID          PRIMARY KEY  DEFAULT uuid_generate_v4(),
    drink_id   UUID          NOT NULL
                REFERENCES drinks(id) ON DELETE CASCADE,
    url        TEXT          NOT NULL,
    position   INT           NOT NULL CHECK (position BETWEEN 1 AND 3),
    created_at TIMESTAMP     NOT NULL DEFAULT NOW(),
    UNIQUE(drink_id, position)
);

/***********************************************************************
 * 5.  Orders  (guest checkout)
 **********************************************************************/
CREATE TABLE orders (
    id          UUID          PRIMARY KEY  DEFAULT uuid_generate_v4(),
    guest_name  TEXT          NOT NULL,
    phone       TEXT,
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

/***********************************************************************
 * 6.  Order items
 **********************************************************************/
CREATE TABLE order_items (
    id         UUID          PRIMARY KEY  DEFAULT uuid_generate_v4(),
    order_id   UUID          NOT NULL
                REFERENCES orders(id) ON DELETE CASCADE,
    drink_id   UUID          NOT NULL
                REFERENCES drinks(id) ON DELETE RESTRICT,
    quantity   INT           NOT NULL CHECK (quantity > 0),
    price      NUMERIC(10,2) NOT NULL,
    UNIQUE(order_id, drink_id)                -- one row per drink per order
);

CREATE INDEX idx_order_items_order  ON order_items(order_id);
CREATE INDEX idx_order_items_drink  ON order_items(drink_id);

/***********************************************************************
 * 7.  Data integrity helper (optional)
 *     Enforce “max 3 images / drink” at DB-level as an extra guard.
 **********************************************************************/
CREATE OR REPLACE FUNCTION trg_check_image_limit() RETURNS TRIGGER AS $$
DECLARE
    img_count INT;
BEGIN
    SELECT COUNT(*) INTO img_count
      FROM drink_images
      WHERE drink_id = NEW.drink_id;

    IF TG_OP = 'INSERT' AND img_count >= 3 THEN
        RAISE EXCEPTION 'A drink may have at most 3 images';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_img_limit
   BEFORE INSERT ON drink_images
   FOR EACH ROW
   EXECUTE PROCEDURE trg_check_image_limit();
