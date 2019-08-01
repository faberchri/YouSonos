import React from "react";
import {playTrack, togglePlayPause, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import TrackListEntry from "./TrackListEntry";
import AddToPlaylistButton from "./AddToPlaylistButton";


interface State {
}

const styles = (theme: Theme) => createStyles({});

interface Props extends WithStyles<typeof styles> {
    key: number;
    currentTrack: Track;
    searchResultTrack: Track;
}

class SearchResultEntry extends React.Component<Props, State> {

    render() {

        const searchResultTrack = this.props.searchResultTrack;
        const activeTrack = this.props.currentTrack;

        let showAsPlaying = false;
        let showAsCurrent = false;
        let playPauseCallback = () => playTrack(searchResultTrack.url);
        if (searchResultTrack.url === activeTrack.url) {
            showAsPlaying = activeTrack.track_status === 'PLAYING';
            showAsCurrent = true;
            playPauseCallback = () => togglePlayPause();
        }

        return <TrackListEntry
            track={searchResultTrack}
            showAsCurrent={showAsCurrent}
            showAsPlaying={showAsPlaying}
            playPauseCallback={playPauseCallback}
            rightIcon={ <AddToPlaylistButton track={searchResultTrack} /> }
        />
    }
}

export default withStyles(styles)(SearchResultEntry);
