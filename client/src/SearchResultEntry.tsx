import React from "react";
import {addTrackToPlaylist, playTrack, togglePlayPause, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import IconButton from '@material-ui/core/IconButton';

import Add from '@material-ui/icons/PlaylistAddRounded';
import AddCheck from '@material-ui/icons/PlaylistAddCheckRounded';
import TrackListEntry from "./TrackListEntry";


interface State {
}

const styles = (theme: Theme) => createStyles({});

interface Props extends WithStyles<typeof styles> {
    currentTrack: Track;
    searchResultTrack: Track;
    playlistTrackUrls: ReadonlySet<string>;
}

class SearchResultEntry extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
    }

    render() {

        const {classes} = this.props;

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
            rightIcon={
                <IconButton color="primary" onClick={() => addTrackToPlaylist(searchResultTrack.url)}>
                    {this.props.playlistTrackUrls.has(searchResultTrack.url) ?
                        <AddCheck fontSize="small"/> : <Add fontSize="small"/>}
                </IconButton>
            }
        />
    }
}

export default withStyles(styles)(SearchResultEntry);
