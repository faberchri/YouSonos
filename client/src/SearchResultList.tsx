import React from "react";
import {currentTrack, NULL_TRACK, playlistChanged, PlaylistItem, searchResults, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import SearchResultEntry from "./SearchResultEntry";


interface State {
    searchResultTracks: Track[];
    playlistTrackUrls: ReadonlySet<string>;
    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    list: {
        overflowY: 'auto'
    },
});

interface Props extends WithStyles<typeof styles> {
}

class SearchResultList extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = {
            currentTrack: NULL_TRACK,
            searchResultTracks: [],
            playlistTrackUrls: new Set()
        };
        this.setSearchResults = this.setSearchResults.bind(this);
        this.setPlaylistTrackUrls = this.setPlaylistTrackUrls.bind(this);
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
    }

    componentDidMount() {
        searchResults(this.setSearchResults);
        playlistChanged(this.setPlaylistTrackUrls);
        currentTrack(this.setCurrentTrack)
    }

    setSearchResults(searchResultTracks: Track[]) {
        this.setState({
            searchResultTracks: searchResultTracks,
            playlistTrackUrls: this.state.playlistTrackUrls,
            currentTrack: this.state.currentTrack,
        });
    }

    setPlaylistTrackUrls(items: PlaylistItem[]) {
        const playlistTrackUrls = new Set(items.map(item => item.track.url));
        this.setState({
            searchResultTracks: this.state.searchResultTracks,
            playlistTrackUrls: playlistTrackUrls,
            currentTrack: this.state.currentTrack,
        });
    }

    setCurrentTrack(currentTrack: Track) {
        this.setState({
            searchResultTracks: this.state.searchResultTracks,
            playlistTrackUrls: this.state.playlistTrackUrls,
            currentTrack: currentTrack,
        });
    }

    render() {

        const {classes} = this.props;

        return (
            <List dense className={classes.list}>
                {this.state.searchResultTracks.map(searchResultTrack => <SearchResultEntry
                    searchResultTrack={searchResultTrack}
                    currentTrack={this.state.currentTrack}
                    playlistTrackUrls={this.state.playlistTrackUrls}/>)}
            </List>
        );
    }
}

export default withStyles(styles)(SearchResultList);
