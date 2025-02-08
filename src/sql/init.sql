DROP TABLE recordings CASCADE;
DROP TABLE fragments;

-- Create TABLE recordings
CREATE TABLE recordings (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "owner_id" UUID,
    "created_at" TIMESTAMPTZ DEFAULT now(),
    "sample_rate" INTEGER,
    "channel_count" SMALLINT,
    "file_extension" TEXT
);

-- Create TABLE fragments
CREATE TABLE fragments (
    "recording_id" UUID NOT NULL,
    "index" SMALLINT NOT NULL,
    "sample_number" INTEGER,
    PRIMARY KEY ("recording_id", "index"),
    CONSTRAINT fk_recording FOREIGN KEY ("recording_id") REFERENCES recordings("id") ON DELETE CASCADE
);