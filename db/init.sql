/***********************************************************************
 * MilkShake core schema
 * Postgres 15+   (uuid-ossp + enum + constraints)
 **********************************************************************/
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

/*--------------------------------------------------
  ENUM: drink_type (easy to extend later)
--------------------------------------------------*/
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'drink_type') THEN
        CREATE TYPE drink_type AS ENUM ('soft', 'milkshake', 'cocktail', 'other');
    END IF;
END $$;

/***********************************************************************
 * 1.  Administrative users
 **********************************************************************/
CREATE TABLE admins (
    id            UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    email         TEXT            NOT NULL UNIQUE,
    password_hash TEXT            NOT NULL,
    is_active     BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP       NOT NULL DEFAULT NOW()
);

/***********************************************************************
 * 2.  Item masters (sortable)
 **********************************************************************/
CREATE TABLE item_masters (
    id          UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    name        TEXT            NOT NULL UNIQUE,
    sort_order  INT             NOT NULL DEFAULT 0,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_item_masters_sort ON item_masters(sort_order);

/***********************************************************************
 * 3.  Drinks
 **********************************************************************/
CREATE TABLE drinks (
    id           UUID            PRIMARY KEY  DEFAULT uuid_generate_v4(),
    name         TEXT            NOT NULL,
    description  TEXT,
    price        NUMERIC(10,2)   NOT NULL CHECK (price >= 0),
    type         drink_type      NOT NULL DEFAULT 'other',
    image_cover  TEXT,
    created_at   TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drinks_type ON drinks(type);

/***********************************************************************
 * 4.  Item master assignments (many-to-many)
 **********************************************************************/
CREATE TABLE item_master_drinks (
    item_master_id UUID NOT NULL
        REFERENCES item_masters(id) ON DELETE CASCADE,
    drink_id       UUID NOT NULL
        REFERENCES drinks(id) ON DELETE CASCADE,
    PRIMARY KEY (item_master_id, drink_id)
);

/***********************************************************************
 * 5.  Drink images (max 3 per drink)
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
 * 6.  Orders (guest checkout)
 **********************************************************************/
CREATE TABLE orders (
    id          UUID          PRIMARY KEY  DEFAULT uuid_generate_v4(),
    guest_name  TEXT          NOT NULL,
    phone       TEXT,
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

/***********************************************************************
 * 7.  Order items
 **********************************************************************/
CREATE TABLE order_items (
    id         UUID          PRIMARY KEY  DEFAULT uuid_generate_v4(),
    order_id   UUID          NOT NULL
                REFERENCES orders(id) ON DELETE CASCADE,
    drink_id   UUID          NOT NULL
                REFERENCES drinks(id) ON DELETE RESTRICT,
    quantity   INT           NOT NULL CHECK (quantity > 0),
    price      NUMERIC(10,2) NOT NULL,
    UNIQUE(order_id, drink_id)
);

CREATE INDEX idx_order_items_order  ON order_items(order_id);
CREATE INDEX idx_order_items_drink  ON order_items(drink_id);

/***********************************************************************
 * 8.  Data integrity helper (optional)
 *     Enforce max 3 images / drink at DB-level as an extra guard.
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
