import React from "react";
import {
    addTrackToPlaylist,
    currentTrack,
    NULL_TRACK,
    playlistChanged,
    PlaylistItem,
    playTrack,
    searchResults,
    searchTracks,
    togglePlayPause,
    Track
} from "./api";
import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import TextField from '@material-ui/core/TextField';
import classNames from 'classnames';
import List from '@material-ui/core/List';
import IconButton from '@material-ui/core/IconButton';

import Add from '@material-ui/icons/PlaylistAddRounded';
import AddCheck from '@material-ui/icons/PlaylistAddCheckRounded';

import CircularProgress from '@material-ui/core/CircularProgress';
import InputAdornment from '@material-ui/core/InputAdornment';

import Clear from '@material-ui/icons/Clear';
import TrackListEntry from "./TrackListEntry";


enum UiState {initial, searchInProgress, showResults}

interface State {
    results: Track[];
    uiState: UiState;
    searchString: string;
    playlistTrackUrls: ReadonlySet<string>;
    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    root: {
        display: 'flex',
        flexFlow: 'column',
    },
    textField: {
        minHeight: '50px',
        width: '100%',
        marginTop: '12px',
        marginBottom: '8px',
    },
    progress: {},
    dense: {},
    list: {
        overflowY: 'auto'
    },
});

interface Props extends WithStyles<typeof styles> {
}

class SearchInput extends React.Component<Props, State> {

    subject = new Subject<string>();

    constructor(props: Props) {
        super(props);
        this.state = SearchInput.getNullSearchResults(new Set(), NULL_TRACK);
        this.setSearchResults = this.setSearchResults.bind(this);
        this.runSearch = this.runSearch.bind(this);
        this.reset = this.reset.bind(this);
        this.showResultList = this.showResultList.bind(this);
        this.indicateError = this.indicateError.bind(this);
        this.setPlaylistTrackUrls = this.setPlaylistTrackUrls.bind(this);
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
        this.searchResultEntry = this.searchResultEntry.bind(this);


        this.subject
            .pipe(debounce(() => timer(500)))
            .subscribe((url) => searchTracks(url));
    }

    componentDidMount() {
        searchResults(this.setSearchResults);
        playlistChanged(this.setPlaylistTrackUrls);
        currentTrack(this.setCurrentTrack)
    }

    setSearchResults(data: Track[]) {
        this.setState({results: data, uiState: UiState.showResults, searchString: this.state.searchString});
    }

    runSearch(event: any) {
        this.setState({results: [], uiState: UiState.searchInProgress, searchString: event.target.value});
        this.subject.next(event.target.value);
    }

    reset() {
        this.setState(SearchInput.getNullSearchResults(this.state.playlistTrackUrls, this.state.currentTrack));
    }

    setPlaylistTrackUrls(items: PlaylistItem[]) {
        const playlistTrackUrls = new Set(items.map(item => item.track.url));
        this.setState({
            results: this.state.results,
            uiState: this.state.uiState,
            searchString: this.state.searchString,
            playlistTrackUrls: playlistTrackUrls,
            currentTrack: this.state.currentTrack,
        });
    }

    setCurrentTrack(track: Track) {
        this.setState({
            results: this.state.results,
            uiState: this.state.uiState,
            searchString: this.state.searchString,
            playlistTrackUrls: this.state.playlistTrackUrls,
            currentTrack: track,
        });
    }

    static getNullSearchResults(playlistTrackUrls: ReadonlySet<string>, currentTrack: Track): State {
        return {
            results: [],
            uiState: UiState.initial,
            searchString: '',
            playlistTrackUrls: playlistTrackUrls,
            currentTrack: currentTrack
        };
    }

    showResultList() {
        return this.state.uiState === UiState.showResults && this.state.results.length > 0
    }

    indicateError() {
        return this.state.uiState === UiState.showResults && this.state.results.length === 0;
    }

    searchResultEntry(track: Track): JSX.Element {
        const {classes} = this.props;

        let showAsPlaying = false;
        let showAsCurrent = false;
        let playPauseCallback = () => playTrack(track.url);
        if (this.state.currentTrack.url === track.url) {
            showAsPlaying = this.state.currentTrack.track_status === 'PLAYING';
            showAsCurrent = true;
            playPauseCallback = () => togglePlayPause();
        }

        return <TrackListEntry
            showAsPlaying={showAsPlaying}
            track={track}
            rightIcon={
                <IconButton color="primary" onClick={() => addTrackToPlaylist(track.url)}>
                    {this.state.playlistTrackUrls.has(track.url) ? <AddCheck fontSize="small"/> :
                        <Add fontSize="small"/>}
                </IconButton>
            }
            playPauseCallback={playPauseCallback}
            showAsCurrent={showAsCurrent}/>
    }

    render() {

        const {classes} = this.props;

        let textFieldAction;
        if (this.state.uiState === UiState.searchInProgress) {
            textFieldAction =
                <CircularProgress className={classes.progress} size={30}/>
        } else {
            if (this.state.searchString.length > 0) {
                textFieldAction =
                    <IconButton
                        aria-label="clear input"
                        onClick={this.reset}>
                        <Clear/>
                    </IconButton>
            }
        }

        let endAdornment;
        if (textFieldAction !== undefined) {
            endAdornment = {
                endAdornment: (
                    <InputAdornment position="end">
                        {textFieldAction}
                    </InputAdornment>
                ),
            };
        }

        let resultList;
        if (this.showResultList()) {
            resultList =
                <List dense className={classes.list}>
                    {this.state.results.map(this.searchResultEntry)}
                </List>
        }

        return (
            <div className={classes.root}>
                <TextField
                    error={this.indicateError()}
                    label="YouTube-URL"
                    className={classNames(classes.textField, classes.dense)}
                    margin="dense"
                    variant="outlined"
                    onChange={this.runSearch}
                    value={this.state.searchString}
                    InputProps={endAdornment}
                />
                {resultList}
            </div>
        );
    }
}

export default withStyles(styles)(SearchInput);
